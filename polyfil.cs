
using System.Collections.Generic;
using UnityEngine;

public class PolyFill : MonoBehaviour
{
    const float EPS = 1e-5f;

    static float SignedArea(List<Vector2> p)
    {
        double a = 0;
        for (int i = 0, j = p.Count - 1; i < p.Count; j = i++)
            a += (double)p[j].x * p[i].y - (double)p[i].x * p[j].y;
        return (float)(a * 0.5);
    }

    static bool Colinear(Vector2 a, Vector2 b, Vector2 c)
    {
        return Mathf.Abs((b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)) <= EPS;
    }

    static bool PointInTri(Vector2 p, Vector2 a, Vector2 b, Vector2 c)
    {
        float s1 = (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x);
        float s2 = (c.x - b.x) * (p.y - b.y) - (c.y - b.y) * (p.x - b.x);
        float s3 = (a.x - c.x) * (p.y - c.y) - (a.y - c.y) * (p.x - c.x);
        bool hasNeg = (s1 < -EPS) || (s2 < -EPS) || (s3 < -EPS);
        bool hasPos = (s1 > EPS) || (s2 > EPS) || (s3 > EPS);
        return !(hasNeg && hasPos);
    }

    static bool IsConvex(Vector2 prev, Vector2 curr, Vector2 next, float orient)
    {
        float cross = (curr.x - prev.x) * (next.y - prev.y) - (curr.y - prev.y) * (next.x - prev.x);
        return orient > 0 ? cross > EPS : cross < -EPS;
    }

    static void RemoveDuplicatesAndColinear(List<Vector2> pts)
    {
        if (pts.Count < 3) return;
        for (int i = pts.Count - 1; i > 0; --i)
            if ((pts[i] - pts[i - 1]).sqrMagnitude < EPS * EPS) pts.RemoveAt(i);
        if ((pts[0] - pts[pts.Count - 1]).sqrMagnitude < EPS * EPS) pts.RemoveAt(pts.Count - 1);
        if (pts.Count < 3) return;
        int k = 0;
        var outPts = new List<Vector2>(pts.Count);
        for (int i = 0; i < pts.Count; i++)
        {
            int prev = (i - 1 + pts.Count) % pts.Count;
            int next = (i + 1) % pts.Count;
            if (!Colinear(pts[prev], pts[i], pts[next])) outPts.Add(pts[i]);
        }
        pts.Clear(); pts.AddRange(outPts);
    }

    public void CreateFilledMesh(List<Vector3> points)
    {
        if (points == null || points.Count < 3) return;

        var pts2 = new List<Vector2>(points.Count);
        for (int i = 0; i < points.Count; i++) pts2.Add(new Vector2(points[i].x, points[i].y));
        RemoveDuplicatesAndColinear(pts2);
        if (pts2.Count < 3) return;

        float area = SignedArea(pts2);
        if (area < 0) pts2.Reverse();

        var verts = new List<Vector3>(pts2.Count);
        for (int i = 0; i < pts2.Count; i++) verts.Add(new Vector3(pts2[i].x, pts2[i].y, 0));

        var V = new List<int>(pts2.Count);
        for (int i = 0; i < pts2.Count; i++) V.Add(i);

        var tris = new List<int>(pts2.Count * 3);
        int guard = 0;

        while (V.Count > 2 && guard < 10000)
        {
            guard++;
            bool earFound = false;
            for (int i = 0; i < V.Count; i++)
            {
                int i0 = V[(i - 1 + V.Count) % V.Count];
                int i1 = V[i];
                int i2 = V[(i + 1) % V.Count];

                Vector2 a = pts2[i0], b = pts2[i1], c = pts2[i2];
                if (!IsConvex(a, b, c, 1f)) continue;

                bool contains = false;
                for (int j = 0; j < V.Count; j++)
                {
                    int idx = V[j];
                    if (idx == i0 || idx == i1 || idx == i2) continue;
                    if (PointInTri(pts2[idx], a, b, c)) { contains = true; break; }
                }
                if (contains) continue;

                tris.Add(i0); tris.Add(i1); tris.Add(i2);
                V.RemoveAt(i);
                earFound = true;
                break;
            }
            if (!earFound) break;
        }

        if (tris.Count < 3) return;

        var mesh = new Mesh { name = "FilledLoopMesh" };
        mesh.SetVertices(verts);
        mesh.SetTriangles(tris, 0);
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();

        var mf = GetComponent<MeshFilter>(); if (mf == null) mf = gameObject.AddComponent<MeshFilter>();
        mf.sharedMesh = mesh;

        var mr = GetComponent<MeshRenderer>(); if (mr == null) mr = gameObject.AddComponent<MeshRenderer>();
        if (mr.sharedMaterial == null)
        {
            var mat = new Material(Shader.Find("Unlit/Color"));
            mat.color = new Color(0.2f, 0.8f, 1f, 0.3f);
            mr.sharedMaterial = mat;
        }
    }
}
