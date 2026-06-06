using UnityEngine;

public class SendToArduino : MonoBehaviour
{
    private SerialController serialController;
    private bool arduinoConnected = false;

    void Start()
    {
        serialController = FindObjectOfType<SerialController>();
        if (serialController == null)
        {
            Debug.LogError("No SerialController found in the scene!");
        }
    }

    void Update()
    {
        if (serialController == null)
            return;

        string message = serialController.ReadSerialMessage();

        if (message != null)
        {
            if (message == SerialController.SERIAL_DEVICE_CONNECTED)
            {
                arduinoConnected = true;
                Debug.Log("Arduino connected");
            }
            else if (message == SerialController.SERIAL_DEVICE_DISCONNECTED)
            {
                arduinoConnected = false;
                Debug.Log("Arduino disconnected");
            }
            else if (message.StartsWith("ACK:"))
            {
                string ackMessage = message.Substring(4);
                Debug.Log("Arduino confirmed receipt: " + ackMessage);
            }
            else
            {
                Debug.Log("Message from Arduino: " + message);
            }
        }

        if (arduinoConnected && Input.GetKeyDown(KeyCode.Space))
        {
            string msgToSend = "HELLO";
            serialController.SendSerialMessage(msgToSend);
            Debug.Log("Sent message to Arduino: " + msgToSend);
        }
    }
}