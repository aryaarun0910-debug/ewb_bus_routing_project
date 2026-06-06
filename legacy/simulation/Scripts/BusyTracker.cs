// using UnityEngine;
// using UnityEngine.UI;

// public class BusyTracker : MonoBehaviour
// {
//     [SerializeField] GameObject bus;
//     [SerializeField] int personCount;
//     [SerializeField] Text textBox;
//     int personThreshold = 10;
//     float timer;

//     // Start is called once before the first execution of Update after the MonoBehaviour is created
//     void Start()
//     {
        
//     }

//     // Update is called once per frame
//     void Update()
//     {
//         timer += Time.deltaTime;

//         if (timer >= 1f)
//         {
//             personCount++;
//             timer = 0f;
//         }

//         if(personCount > personThreshold)
//         {
//             bus.GetComponent<Movement>().addStop(this.gameObject);
//         }

//         textBox.text = personCount.ToString();
//     }
// }
