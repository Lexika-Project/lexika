const urlParam = new URLSearchParams(window.location.search);
const livre = urlParam.get("livre");
const numPage = parseInt(urlParam.get("page"));
const showBox = urlParam.get("showBox") === "true";
const langue = urlParam.get("langue");
const sens = urlParam.get("sens");
const ALLOWED_EXTENTION = ["mp3", "wav"];
const MAX_NUM_PAGE = 274;

let box = 0;
let audio = null;
let mot;
let audioFileInput = document.querySelector("#audioFile");
let fileStatus = document.querySelector("#fileStatus");
let audiosearch = document.querySelector("#audiosearch");
let audiobtn = document.querySelector("#audioadd");
let editButton = document.querySelector("#edit");
let sendButton = document.querySelector("#send");
let reference = document.querySelector("#reference");
let boxbtn = document.querySelector("#boxbtn");

sendButton.disabled = true;

let livreBox = livre + "-rectangle";
let livreStart = livre;

document.querySelector("#pdfViewer").src = `static/pdf/${livreStart}.pdf#page=${numPage}&zoom=140`;

function createTable(data) {
    const table = document.querySelector("#resultHistory");
    const head = document.querySelector("#resulthead");

    let trHead = document.createElement("tr");

    let thLivre = document.createElement("th");
    thLivre.textContent = "Livre";
    trHead.appendChild(thLivre);
    let thLangue = document.createElement("th");
    thLangue.textContent = "Langue";
    trHead.appendChild(thLangue);
    let thMot = document.createElement("th");
    thMot.textContent = "Mot";
    trHead.appendChild(thMot);
    let thPage = document.createElement("th");
    thPage.textContent = "Page";
    trHead.appendChild(thPage);

    head.appendChild(trHead);

    let firstRow = data[0];

    let tr = document.createElement("tr");
    
    let tdLivre = document.createElement("td");
    tdLivre.textContent = livre;
    tr.appendChild(tdLivre);

    let tdLangue = document.createElement("td");
    tdLangue.textContent = langue;
    tr.appendChild(tdLangue);

    let tdRenvoyer = document.createElement("td");
    tdRenvoyer.textContent = firstRow[1];

    if (audio !== null && audio !== undefined) {

        const button = document.createElement("button");
        button.innerHTML = '<i id="soundbtn" class="fa fa-volume-up"></i>';
        button.onclick = playSound;
        tdRenvoyer.appendChild(button);
    }

    tr.appendChild(tdRenvoyer);


    let tdNumPage = document.createElement("td");
    tdNumPage.textContent = numPage;
    tr.appendChild(tdNumPage);
    
    table.appendChild(tr);
}

fetch("/getaudio", {
    method: "POST",
    headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
    },
    body: JSON.stringify({
        langue: langue,
        sens: sens,
    }),
})
.then((resp) => resp.json()) // Utiliser resp.json() au lieu de resp.text()
.then((data) => {
    audio = data[0][0]; // Accéder à la valeur dans la structure de données
    console.log(audio);
})
.catch((error) => {
    console.error('Une erreur est survenue lors de la requête fetch:', error);
});



function sendButtonInit(sendButton) {
    sendButton.addEventListener("click", () => {
      const dataToSend = [[langue, mot, parseInt(sens)]];
  
      fetch("/edit", {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(dataToSend),
      })
        .then((response) => {
          if (response.ok) {
            sendButton.innerHTML = `<i class="fa-solid fa-check" style="color: #ffffff;"></i>`;
            setTimeout(() => {
              sendButton.innerHTML = `<i class="fa-regular fa-floppy-disk"></i>`;
            }, 1000);
          } else {
            throw new Error('Network response was not ok');
          }
        })
        .then(() => {
          console.log('Request succeeded');
        })
        .catch((error) => {
          console.error('There has been a problem with your fetch operation:', error);
        });
    });
  }
  


sendButtonInit(sendButton);





fetch("/getreference", {
    method: "POST",
    headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
    },
    body: JSON.stringify({
        livre: livre,
    }),
})
.then((resp) => resp.json()) // Utiliser resp.json() au lieu de resp.text()
.then((data) => {
    const text = data[0][0]; // Accéder à la valeur dans la structure de données
    reference.innerHTML = text;
});


fetch("/historyRequest", {
    method: "POST",
    headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
    },
    body: JSON.stringify({
        langue: langue,
        sens: sens,
    }),
})
.then((resp) => {
    return resp.json();
})
.then((json) => {
    createTable(json);
});


  

const dragBox = document.querySelector(".drag-audio");
dragBox.addEventListener("dragenter", (_) => {
	dragBox.classList.add("drag-audio-enter");
});
dragBox.addEventListener("dragleave", (_) => {
	dragBox.classList.remove("drag-audio-enter");
});

document.addEventListener("dragover", (event) => {
	event.preventDefault();
});
document.addEventListener("drop", (event) => {
	event.preventDefault();
});

audiosearch.addEventListener("click", function() {
    audioFileInput.click();
});

const popupError = document.querySelector("#unsupported-extention-popup");
audioFileInput.addEventListener("change", function() {
    let file = this.files[0];
    let name_split = file.name.split(".");
    let extention = name_split.pop();
    if (ALLOWED_EXTENTION.includes(extention.toLowerCase())) {
        const data = new FormData();
        data.append("file", file);
        data.append("sens", sens);
        data.append("langue", langue);
        fetch("/receiveAudio", {
            method: "POST",
            body: data,
        }).then((resp) => {
            console.log(resp);
            // Ici, vous pouvez ajouter du code pour afficher le nom du fichier dans le h2
            fileStatus.textContent = 'Fichier téléchargé avec succès : ' + file.name;
        });
    } else {
        // Afficher une erreur si l'extension n'est pas autorisée
        popupError.innerText = `L'extension ${extention} n'est pas prise en charge.`;
        popupError.hidden = false;
        setTimeout((_) => {
            popupError.hidden = true;
        }, 5000);
    }
});

dragBox.addEventListener("drop", (event) => {
    event.preventDefault();
    dragBox.classList.remove("drag-audio-enter");
    
    let file = event.dataTransfer.files[0];
    let name_split = file.name.split(".");
    let extention = name_split.pop();
    if (ALLOWED_EXTENTION.includes(extention.toLowerCase())) {
        const data = new FormData();
        data.append("file", file);
        data.append("sens", sens);
        data.append("langue", langue);
        fetch("/receiveAudio", {
            method: "POST",
            body: data,
        }).then((resp) => {
            console.log(resp);
            // Ici, vous pouvez ajouter du code pour afficher le nom du fichier dans le h2
            fileStatus.textContent = 'Fichier téléchargé avec succès : ' + file.name;
        });
    } else {
        // Afficher une erreur si l'extension n'est pas autorisée
        popupError.innerText = `L'extension ${extention} n'est pas prise en charge.`;
        popupError.hidden = false;
        setTimeout((_) => {
            popupError.hidden = true;
        }, 5000);
    }
});


function changePdfBox() {
    if (box === 1) {
        document.querySelector(
            "#pdfViewer"
        ).src = `static/pdf/${livreBox}.pdf#page=${numPage}&zoom=140`;
    } else if(box === 0) {
        document.querySelector(
            "#pdfViewer"
        ).src = `static/pdf/${livre}.pdf#page=${numPage}&zoom=140`;
    }
}

boxbtn.addEventListener("click", function() {

    if (box === 0) {
        box = 1;
        changePdfBox();
    } else if (box === 1) {
       box = 0;
       changePdfBox();
    }

});

function playSound(event) {
	let button = event.target;
	if (button.tagName !== "BUTTON") {
		button = button.parentElement;
	}
	playSound?.currentSound?.pause();
	playSound.currentSound = new Audio("/static/audio/" + audio);
	playSound.currentSound.play();
}


// Function to handle cell editing
function editCell(td) {
    // Save the original text
    let originalText = td.textContent;

    // Replace the cell content with an input element
    td.textContent = "";
    let input = document.createElement("input");
    input.type = "text";
    input.value = originalText;
    td.appendChild(input);

    // Handle input change in the input field
    input.addEventListener("input", function() {
        // Update the variable every time the input field changes
        mot = input.value;
        sendButton.disabled = false;
    });

    // Handle Enter key in the input field
    input.addEventListener("keydown", function(event) {
        if (event.key === "Enter") {
            // Replace the input field with the entered text
            let newText = input.value;
            td.textContent = newText;
        }
    });

    // Focus the input field
    input.focus();
}


// Add event listener to the edit button
editButton.addEventListener("click", function() {
    // Get the renvoyer cell of the last row
    let tdRenvoyer = document.querySelector("#resultHistory tr:last-child td:nth-child(3)");

    // Start editing the cell
    editCell(tdRenvoyer);
});



audiobtn.addEventListener("click", function() {

    if (dragBox.style.display === 'none') {
        dragBox.style.display = 'flex';
    } else {
        dragBox.style.display = 'none';
    }

});