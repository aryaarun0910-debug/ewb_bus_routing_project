using UnityEngine;

public class BusToggle : MonoBehaviour
{
    public void toggleBus(bool isOn)
    {
        gameObject.SetActive(isOn);
    }
}
