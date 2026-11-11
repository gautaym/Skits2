using System;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

/// <summary>
/// Headless environment check for making video skits with Unity.
/// Run with: Unity -batchmode -projectPath . -executeMethod SkitEnvCheck.Run
/// Writes Output/report.txt and a PNG frame sequence to Output/frames.
/// </summary>
public static class SkitEnvCheck
{
    const int Width = 720;   // vertical 9:16, Shorts/Reels format
    const int Height = 1280;
    const int Fps = 24;
    const int FrameCount = Fps * 3;

    static readonly StringBuilder Report = new StringBuilder();
    static bool allPassed = true;

    static void Line(string s)
    {
        Report.AppendLine(s);
        Debug.Log("[SkitEnvCheck] " + s);
    }

    static void Check(string name, bool pass, string detail)
    {
        if (!pass) allPassed = false;
        Line($"{(pass ? "PASS" : "FAIL")} | {name} | {detail}");
    }

    static Type FindType(string fullName) =>
        AppDomain.CurrentDomain.GetAssemblies()
            .Select(a => a.GetType(fullName, false))
            .FirstOrDefault(t => t != null);

    public static void Run()
    {
        var outDir = Environment.GetEnvironmentVariable("SKIT_OUT");
        if (string.IsNullOrEmpty(outDir)) outDir = Path.GetFullPath("Output");
        var framesDir = Path.Combine(outDir, "frames");
        Directory.CreateDirectory(framesDir);

        try
        {
            Line("== System ==");
            Line($"Unity version : {Application.unityVersion}");
            Line($"OS            : {SystemInfo.operatingSystem}");
            Line($"CPU           : {SystemInfo.processorType} x{SystemInfo.processorCount}");
            Line($"RAM           : {SystemInfo.systemMemorySize} MB");
            Line($"GPU           : {SystemInfo.graphicsDeviceName} ({SystemInfo.graphicsDeviceType}, {SystemInfo.graphicsDeviceVersion})");
            Line("");
            Line("== Checks ==");

            Check("Graphics device (needed to render frames)",
                SystemInfo.graphicsDeviceType != GraphicsDeviceType.Null,
                SystemInfo.graphicsDeviceType.ToString());

            var pkgs = UnityEditor.PackageManager.PackageInfo.GetAllRegisteredPackages();
            foreach (var id in new[] { "com.unity.timeline", "com.unity.cinemachine", "com.unity.recorder", "com.unity.ugui" })
            {
                var p = pkgs.FirstOrDefault(x => x.name == id);
                Check($"Package {id}", p != null, p != null ? p.version : "not installed");
            }

            CheckType("Timeline API", "UnityEngine.Timeline.TimelineAsset", createInstance: true);
            CheckType("Cinemachine API", "Unity.Cinemachine.CinemachineCamera", createInstance: false);
            CheckType("Recorder API", "UnityEditor.Recorder.RecorderController", createInstance: false);
            CheckType("TextMeshPro API", "TMPro.TextMeshPro", createInstance: false);

            RenderTestSkit(framesDir);
        }
        catch (Exception e)
        {
            Check("Unexpected exception", false, e.ToString());
        }

        Line("");
        Line(allPassed ? "RESULT: ALL UNITY CHECKS PASSED" : "RESULT: SOME UNITY CHECKS FAILED");
        File.WriteAllText(Path.Combine(outDir, "unity-report.txt"), Report.ToString());
        EditorApplication.Exit(allPassed ? 0 : 1);
    }

    static void CheckType(string label, string fullName, bool createInstance)
    {
        var t = FindType(fullName);
        if (t == null) { Check(label, false, $"{fullName} not found"); return; }
        if (createInstance && typeof(ScriptableObject).IsAssignableFrom(t))
        {
            var inst = ScriptableObject.CreateInstance(t);
            Check(label, inst != null, inst != null ? $"created {t.Name}" : "CreateInstance returned null");
            if (inst != null) UnityEngine.Object.DestroyImmediate(inst);
            return;
        }
        Check(label, true, $"{fullName} available");
    }

    static Material Mat(Color c)
    {
        var shader = Shader.Find("Standard") ?? Shader.Find("Universal Render Pipeline/Lit");
        return new Material(shader) { color = c };
    }

    static (Transform body, Transform head) MakeCharacter(string name, Color color, Vector3 pos)
    {
        var root = new GameObject(name).transform;
        root.position = pos;
        var body = GameObject.CreatePrimitive(PrimitiveType.Capsule).transform;
        body.SetParent(root, false);
        body.localPosition = new Vector3(0, 1, 0);
        body.GetComponent<Renderer>().sharedMaterial = Mat(color);
        var head = GameObject.CreatePrimitive(PrimitiveType.Sphere).transform;
        head.SetParent(root, false);
        head.localPosition = new Vector3(0, 2.3f, 0);
        head.localScale = Vector3.one * 0.8f;
        head.GetComponent<Renderer>().sharedMaterial = Mat(new Color(1f, 0.85f, 0.7f));
        return (root, head);
    }

    /// <summary>Builds a tiny two-character scene and renders it frame by frame to PNGs.</summary>
    static void RenderTestSkit(string framesDir)
    {
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        var bg = new Color(0.12f, 0.14f, 0.2f);
        var camGo = new GameObject("Camera");
        var cam = camGo.AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = bg;
        cam.fieldOfView = 50;

        var light = new GameObject("Sun").AddComponent<Light>();
        light.type = LightType.Directional;
        light.intensity = 1.2f;
        light.shadows = LightShadows.Soft;
        light.transform.rotation = Quaternion.Euler(45, -30, 0);

        var ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
        ground.transform.localScale = new Vector3(3, 1, 3);
        ground.GetComponent<Renderer>().sharedMaterial = Mat(new Color(0.3f, 0.55f, 0.3f));

        var a = MakeCharacter("Actor A", new Color(0.9f, 0.3f, 0.3f), new Vector3(-1.5f, 0, 0));
        var b = MakeCharacter("Actor B", new Color(0.3f, 0.45f, 0.95f), new Vector3(1.5f, 0, 0));

        var caption = new GameObject("Caption").AddComponent<TextMesh>();
        var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        caption.font = font;
        caption.GetComponent<MeshRenderer>().sharedMaterial = font.material;
        caption.text = "Skits2 render test";
        caption.characterSize = 0.12f;
        caption.fontSize = 64;
        caption.anchor = TextAnchor.MiddleCenter;
        caption.color = Color.white;
        caption.transform.position = new Vector3(0, 4.2f, 0);

        var rt = new RenderTexture(Width, Height, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
        cam.targetTexture = rt;
        var tex = new Texture2D(Width, Height, TextureFormat.RGB24, false);

        int nonBackgroundFrames = 0;
        var start = DateTime.UtcNow;
        for (int i = 0; i < FrameCount; i++)
        {
            float t = i / (float)Fps;
            // Actors walk toward each other, heads bob as if talking.
            a.body.position = new Vector3(Mathf.Lerp(-2.5f, -0.9f, t / 2f), 0, 0);
            b.body.position = new Vector3(Mathf.Lerp(2.5f, 0.9f, t / 2f), 0, 0);
            a.body.rotation = Quaternion.Euler(0, 90, 0);
            b.body.rotation = Quaternion.Euler(0, -90, 0);
            a.head.localPosition = new Vector3(0, 2.3f + Mathf.Abs(Mathf.Sin(t * 12)) * 0.08f, 0);
            b.head.localPosition = new Vector3(0, 2.3f + Mathf.Abs(Mathf.Sin(t * 9 + 1)) * 0.08f, 0);
            // Slow camera dolly-in.
            camGo.transform.position = new Vector3(Mathf.Sin(t * 0.5f) * 1.5f, 2.2f, Mathf.Lerp(-9f, -6.5f, t / 3f));
            camGo.transform.LookAt(new Vector3(0, 1.8f, 0));
            caption.transform.rotation = camGo.transform.rotation;

            cam.Render();
            RenderTexture.active = rt;
            tex.ReadPixels(new Rect(0, 0, Width, Height), 0, 0);
            tex.Apply();
            RenderTexture.active = null;

            if (HasContent(tex, bg)) nonBackgroundFrames++;
            File.WriteAllBytes(Path.Combine(framesDir, $"frame_{i:D4}.png"), tex.EncodeToPNG());
        }
        var secs = (DateTime.UtcNow - start).TotalSeconds;

        Check("Render frames to PNG", Directory.GetFiles(framesDir, "*.png").Length == FrameCount,
            $"{FrameCount} frames at {Width}x{Height} in {secs:F1}s ({FrameCount / secs:F1} fps)");
        Check("Frames contain rendered scene (not blank)", nonBackgroundFrames == FrameCount,
            $"{nonBackgroundFrames}/{FrameCount} frames have scene content");

        cam.targetTexture = null;
        UnityEngine.Object.DestroyImmediate(rt);
        UnityEngine.Object.DestroyImmediate(tex);
    }

    static bool HasContent(Texture2D tex, Color bg)
    {
        var px = tex.GetPixels32();
        Color32 b = bg;
        int differing = 0;
        for (int i = 0; i < px.Length; i += 37)
        {
            var p = px[i];
            if (Mathf.Abs(p.r - b.r) + Mathf.Abs(p.g - b.g) + Mathf.Abs(p.b - b.b) > 30) differing++;
        }
        return differing > (px.Length / 37) * 0.05f;
    }
}
