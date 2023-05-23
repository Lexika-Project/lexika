const urlParam = new URLSearchParams(window.location.search);
const livre = urlParam.get("livre");
const numPage = parseInt(urlParam.get("page"));
const showBox = urlParam.get("showBox") === "true";
const langue = urlParam.get("langue");
const sens = urlParam.get("sens");
const ALLOWED_EXTENTION = ["mp3", "wav"];
const MAX_NUM_PAGE = 274;

let mot;
let editButton = document.querySelector("#edit");
let sendButton = document.querySelector("#send");
let checkBox = document.querySelector("#showBox");
editButton.hidden = false;
sendButton.hidden = false;


let livreBox = livre + "-rectangle";
let livreStart = livre;
if (showBox) {
    livreStart = livreBox;
}

document.querySelector("#pdfViewer").src = `static/pdf/${livreStart}.pdf#page=${numPage}`;

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


    let lastRow = data[data.length - 1];


    let tr = document.createElement("tr");

    let tdLivre = document.createElement("td");
    tdLivre.textContent = livre;
    tr.appendChild(tdLivre);
    let tdLangue = document.createElement("td");
    tdLangue.textContent = langue;
    tr.appendChild(tdLangue);
    let tdRenvoyer = document.createElement("td");
    tdRenvoyer.textContent = lastRow[1]; // accessing the second element of the array
    tr.appendChild(tdRenvoyer);
    let tdNumPage = document.createElement("td");
    tdNumPage.textContent = numPage;
    tr.appendChild(tdNumPage);

    table.appendChild(tr);
}



function sendButtonInit(sendButton) {
	sendButton.addEventListener("click", (_) => {
		let dataToSend = Array.from(document.querySelectorAll("#resultHistory tr")).map(tr => {
			let date = tr.children[0].innerText;
			let value = tr.children[1].innerText;
			return [date, value];
		});
		fetch("/edit", {
			method: "POST",
			headers: {
				Accept: "application/json",
				"Content-Type": "application/json",
			},
			body: JSON.stringify(dataToSend),
		});
	});
}





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
    console.log(json);
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

const popupError = document.querySelector("#unsupported-extention-popup");
dragBox.addEventListener("drop", (event) => {
	event.preventDefault();
	dragBox.classList.remove("drag-audio-enter");
	const file = event.dataTransfer.files[0];
	const name_split = file.name.split(".");
	const extention = name_split.pop();
	if (ALLOWED_EXTENTION.includes(extention.toLowerCase())) {
		const data = new FormData();
		data.append("file", file);
		data.append("sens", sens);
		data.append("langue", langue);
		console.log(data);
		fetch("/receiveAudio", {
			method: "POST",
			body: data,
		}).then((resp) => {
			console.log(resp);
		});
	} else {
		popupError.innerText = `L'extention ${extention} n'est pas pris en charge.`;
		popupError.hidden = false;
		setTimeout((_) => {
			popupError.hidden = true;
		}, 5000);
	}
});

function changePdfBox(bool) {
    if (checkBox.checked) {
        document.querySelector(
            "#pdfViewer"
        ).src = `static/pdf/${livreBox}.pdf#page=${numPage}`;
    } else {
        document.querySelector(
            "#pdfViewer"
        ).src = `static/pdf/${livre}.pdf#page=${numPage}`;
    }
}

checkBox.addEventListener("click", changePdfBox);
document.querySelector("#labelBox").addEventListener("click", (_) => {
    checkBox.checked = !checkBox.checked;
    changePdfBox();
});


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

    // Handle Enter key in the input field
    input.addEventListener("keydown", function(event) {
        if (event.key === "Enter") {
            // Replace the input field with the entered text
            let newText = input.value;
            td.textContent = newText;

            // Save the entered text in the variable
            mot = newText;
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
