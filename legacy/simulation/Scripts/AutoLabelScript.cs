using UnityEngine;
using TMPro;

public class AutoLabelSpawner : MonoBehaviour
{
    [SerializeField] Vector3 labelOffset = new Vector3(0, 1f, 0);
    [SerializeField] float fontSize = 3f;

    void Start()
    {
        GameObject[] allObjects = FindObjectsOfType<GameObject>();

        foreach (GameObject obj in allObjects)
        {
            if (obj.name.StartsWith("S") || obj.name.StartsWith("Q"))
            {
                CreateLabel(obj);
            }
        }
    }

    void CreateLabel(GameObject target)
    {
        // Prevent duplicate labels
        if (target.transform.Find("Label") != null) return;

        GameObject labelObj = new GameObject("Label");
        labelObj.transform.SetParent(target.transform);
        labelObj.transform.localPosition = labelOffset;

        TextMeshPro tmp = labelObj.AddComponent<TextMeshPro>();
        tmp.text = target.name;
        tmp.fontSize = fontSize;
        tmp.alignment = TextAlignmentOptions.Center;
        tmp.color = Color.black;
        tmp.enableAutoSizing = false;
        tmp.fontSize = fontSize;

        // 🎨 Colour based on name
        if (target.name.StartsWith("S"))
            tmp.color = Color.red;
        else if (target.name.StartsWith("Q"))
            tmp.color = Color.cyan;

        labelObj.AddComponent<Billboard>();
    }
}
