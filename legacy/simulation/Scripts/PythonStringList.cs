using System.Collections.Generic;
using System.Diagnostics;
using UnityEngine;

public class PythonStringList : MonoBehaviour
{
    public string pythonScript = "Assets/StreamingAssets/script_json.py";

    [System.Serializable]
    public class StringListWrapper
    {
        public List<string> items;
    }

    public List<string> pythonPath()
    {
        List<string> stringsFromPython = RunPythonScript(pythonScript);

        foreach (string item in stringsFromPython)
        {
            UnityEngine.Debug.Log(item);
        }

        return stringsFromPython;
    }

    List<string> RunPythonScript(string scriptPath)
    {
        try
        {
            ProcessStartInfo psi = new ProcessStartInfo
            {
                FileName = "python",
                Arguments = scriptPath,
                RedirectStandardOutput = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using (Process process = Process.Start(psi))
            {
                string output = process.StandardOutput.ReadToEnd();
                process.WaitForExit();

                UnityEngine.Debug.Log("Python output: " + output); // check what Python actually prints

                // Deserialize JSON into wrapper
                StringListWrapper wrapper = JsonUtility.FromJson<StringListWrapper>(output);

                if (wrapper == null || wrapper.items == null)
                {
                    UnityEngine.Debug.LogError("Failed to parse JSON from Python output.");
                    return new List<string>();
                }

                return wrapper.items;
            }
        }
        catch (System.Exception e)
        {
            UnityEngine.Debug.LogError("Error running Python script: " + e.Message);
            return new List<string>();
        }
    }
}
