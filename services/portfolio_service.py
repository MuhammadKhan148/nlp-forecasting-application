"""Portfolio management service."""
from __future__ import annotations

import math
import os
from math import sqrt
from statistics import mean, pstdev
from typing import Dict, List

from .config_service import CONFIG


class PortfolioService:
    def __init__(self, db):
        self.db = db
        self.portfolio_name = os.environ.get('PORTFOLIO_NAME', 'Adaptive Portfolio')
        self.strategy = 'adaptive_threshold'
        self.buy_threshold = float(os.environ.get('PORTFOLIO_BUY_THRESHOLD', '0.01'))
        self.sell_threshold = float(os.environ.get('PORTFOLIO_SELL_THRESHOLD', '0.008'))
        self.trade_fraction = float(os.environ.get('PORTFOLIO_TRADE_FRACTION', '0.15'))

    def _ensure(self):
        return self.db.ensure_portfolio(self.portfolio_name, self.strategy, CONFIG.portfolio_initial_cash)

    def _position_map(self, portfolio_id: int) -> Dict[str, Dict]:
        return {pos['symbol']: pos for pos in self.db.get_portfolio_positions(portfolio_id)}

    def _update_position(self, portfolio_id: int, symbol: str, current, quantity: float, price: float):
        if quantity == 0:
            return
        existing = current.get(symbol)
        if not existing:
            self.db.upsert_position(portfolio_id, symbol, quantity, price)
            current[symbol] = {'symbol': symbol, 'quantity': quantity, 'avg_price': price}
            return
        total_qty = existing['quantity'] + quantity
        if total_qty <= 0:
            self.db.upsert_position(portfolio_id, symbol, 0, 0)
            current.pop(symbol, None)
            return
        if quantity > 0:
            avg_price = (existing['quantity'] * existing['avg_price'] + quantity * price) / total_qty
        else:
            avg_price = existing['avg_price']
        self.db.upsert_position(portfolio_id, symbol, total_qty, avg_price)
        current[symbol] = {'symbol': symbol, 'quantity': total_qty, 'avg_price': avg_price}

    def run_auto_strategy(self) -> Dict:
        portfolio = self._ensure()
        positions = self._position_map(portfolio['id'])
        cash = portfolio['cash']
        actions = []

        for symbol in CONFIG.ingest_symbols:
            latest_price = self.db.get_latest_price(symbol)
            forecast = self.db.get_latest_forecast(symbol)
            if not latest_price or not forecast or not forecast.get('predicted_close'):
                continue
            spot = latest_price['close']
            predicted = forecast['predicted_close']
            if not spot:
                continue
            delta = (predicted - spot) / spot
            available_cash = cash * self.trade_fraction
            position = positions.get(symbol)

            if delta >= self.buy_threshold and available_cash > spot:
                quantity = available_cash / spot
                cash -= quantity * spot
                self._update_position(portfolio['id'], symbol, positions, quantity, spot)
                reason = f"Predicted return {delta:.2%} >= {self.buy_threshold:.2%}"
                self.db.record_trade(portfolio['id'], symbol, 'buy', quantity, spot, reason)
                actions.append({'symbol': symbol, 'action': 'buy', 'quantity': quantity, 'price': spot})
            elif delta <= -self.sell_threshold and position:
                quantity = -position['quantity']
                cash += position['quantity'] * spot
                self._update_position(portfolio['id'], symbol, positions, quantity, spot)
                reason = f"Predicted return {delta:.2%} <= -{self.sell_threshold:.2%}"
                self.db.record_trade(portfolio['id'], symbol, 'sell', -quantity, spot, reason)
                actions.append({'symbol': symbol, 'action': 'sell', 'quantity': -quantity, 'price': spot})

        self.db.update_portfolio_cash(portfolio['id'], cash)
        metrics = self._snapshot(portfolio['id'])
        metrics['actions'] = actions
        return metrics

    def _snapshot(self, portfolio_id: int, record: bool = True) -> Dict:
        portfolio = self._ensure()
        positions = self.db.get_portfolio_positions(portfolio_id)
        holdings_value = 0.0
        for pos in positions:
            latest = self.db.get_latest_price(pos['symbol'])
            if latest:
                holdings_value += pos['quantity'] * latest['close']
        equity = portfolio['cash'] + holdings_value
        returns = (equity - portfolio['initial_cash']) / portfolio['initial_cash'] if portfolio['initial_cash'] else 0.0
        history = self.db.get_portfolio_equity_history(portfolio_id, limit=20)
        equities = [row['equity'] for row in history]
        returns_series = []
        for earlier, later in zip(equities[1:], equities[:-1]):
            if earlier:
                returns_series.append((later - earlier) / earlier)
        volatility = pstdev(returns_series) if len(returns_series) >= 2 else 0.0
        avg_return = mean(returns_series) if returns_series else returns
        sharpe = (avg_return / volatility) * sqrt(252) if volatility else 0.0
        if record:
            self.db.record_equity_snapshot(portfolio_id, equity, portfolio['cash'], holdings_value, returns, volatility, sharpe)
        return {
            'portfolio': portfolio,
            'positions': positions,
            'equity': equity,
            'returns': returns,
            'volatility': volatility,
            'sharpe': sharpe,
            'history': history,
            'trades': self.db.get_recent_trades(portfolio_id)
        }

    def manual_trade(self, symbol: str, action: str, quantity: float, price: float | None = None) -> Dict:
        portfolio = self._ensure()
        latest = self.db.get_latest_price(symbol)
        if price is None:
            price = latest['close'] if latest else 0
        if price <= 0:
            raise ValueError('Price unavailable for trade')
        positions = self._position_map(portfolio['id'])
        if action == 'buy':
            cost = quantity * price
            if cost > portfolio['cash']:
                raise ValueError('Insufficient cash')
            portfolio['cash'] -= cost
            self.db.update_portfolio_cash(portfolio['id'], portfolio['cash'])
            self._update_position(portfolio['id'], symbol, positions, quantity, price)
            self.db.record_trade(portfolio['id'], symbol, 'buy', quantity, price, 'manual')
        elif action == 'sell':
            position = positions.get(symbol)
            if not position or position['quantity'] < quantity:
                raise ValueError('Insufficient holdings')
            portfolio['cash'] += quantity * price
            self.db.update_portfolio_cash(portfolio['id'], portfolio['cash'])
            self._update_position(portfolio['id'], symbol, positions, -quantity, price)
            self.db.record_trade(portfolio['id'], symbol, 'sell', quantity, price, 'manual')
        else:
            raise ValueError('Unsupported action')
        return self._snapshot(portfolio['id'])

    def summary(self) -> Dict:
        portfolio = self._ensure()
        return self._snapshot(portfolio['id'], record=False)
