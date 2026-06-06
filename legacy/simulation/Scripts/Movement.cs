using UnityEngine;
using System.Collections;
using System.Collections.Generic;

public class Movement : MonoBehaviour
{
    [SerializeField] float speed = 3f;
    [SerializeField] GameObject pythonRunner;
    [SerializeField] string[] path = new string[26]; // Array of names 
    List<string> pythonPath;
    int pathIndex = 0;

    void Start()
    {
        // // Fill path array with all GameObjects in world with "S..." or "Q..."
        // for (int i = 1; i < 26; i++)
        // {
        //     path[i - 1] = GameObject.Find($"Q{i}");
        //     if (path[i - 1] == null)
        //     {
        //         Debug.LogError($"Q{i} not found!");
        //         enabled = false;
        //         return;
        //     }
        // }
        pythonPath = pythonRunner.GetComponent<PythonStringList>().pythonPath();
        StartCoroutine(FollowPath(pythonPath));
    }

    IEnumerator FollowPath(List<string> names)
    {
        GameObject[] path = new GameObject[names.Count];
        // Fill GameObject path with objsect with the names from the nanmes array
        if(names == null || names.Count == 0)
        {
            yield break;
        }

        for(int i = 0; i < names.Count; i++)
        {
            path[i] = GameObject.Find(names[i]);
            if(path[i] == null)
            {
                break;    
            }
        }
        transform.position = path[0].transform.position;
        while (pathIndex < path.Length)
        {
            Vector3 target = path[pathIndex].transform.position;

            while ((transform.position - target).sqrMagnitude > 0.0001f)
            {
                transform.position = Vector3.MoveTowards(
                    transform.position,
                    target,
                    speed * Time.deltaTime
                );
                yield return null; // wait next frame
            }

            yield return new WaitForSeconds(0.5f);
            pathIndex++;
        }
    }
}
