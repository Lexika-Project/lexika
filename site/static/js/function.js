let editButton = document.querySelector("#edit");
let sendButton = document.querySelector("#send");
let csvButton = document.querySelector("#download-csv")

export function createTableResult(tab, langueBase, listeLangue, resultTitle, resultSearch) {
	let tablediv = document.querySelector("#tableDiv");
	tablediv.style.display = 'table';



	let foot = document.querySelector("#resultBottom");
	resultTitle.innerHTML = "";
	foot.innerHTML="";
	let trTitle = document.createElement("tr");
	let trfoot = document.createElement("tr");
	let th;
	let thx;
	let index = 0;

	for (let langue of listeLangue) {
		th = document.createElement("th");
		thx = document.createElement("th");
		th.innerHTML = `${langue}&nbsp;&nbsp;<i id="az" class="fa-solid fa-arrow-up-a-z" style="color: #ffffff;"></i>`;


		// Utiliser une IIFE pour capturer la valeur actuelle de l'index
		(function(i) {
			th.addEventListener('click', () => sortTable(i));
		})(index);
	
		trTitle.appendChild(th);
		trfoot.appendChild(thx);
		index++;
	}
	

	resultTitle.appendChild(trTitle);
	foot.appendChild(trfoot);
	resultSearch.innerHTML = "";

	for (let ligne of tab) {
		if (ligne !== undefined) {
			let tr = document.createElement("tr");
			let [obj] = ligne.values();
			let sens = obj.sens;
			let td;
			for (let langue of listeLangue) {
				td = document.createElement("td");
				if (ligne.has(langue)) {
					let num = ligne.get(langueBase).numeroPage;
					let livre = ligne.get(langueBase).nomLivre;
					
					if (langue !== "français") {
						td.innerHTML = `<a class="linkHistory"  rel="noopener noreferrer" href="historique?sens=${sens}&langue=${langue}&livre=${livre}&page=${num}&showBox=false">${ligne.get(langue).text}</a>`;
					} else {
						td.innerHTML = `<a class="linkHistory">${ligne.get(langue).text}</a>`;
					}


					if (
						ligne.get(langue).audioLink !== null &&
						ligne.get(langue).audioLink !== undefined
					) {
						const button = document.createElement("button");
						button.innerHTML = '<i id="soundbtn" class="fa fa-volume-up"></i>';
						button.audioLink = ligne.get(langue).audioLink;
						button.onclick = playSound;
						td.appendChild(button);
					}
				}

				td.sens = sens;
				td.langue = langue;
				td.addEventListener("keypress", keyHandler);
				tr.appendChild(td);
			}

			resultSearch.appendChild(tr);
		}
	}
}

function sortTable(n) {
    var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
    table = document.getElementById("table");
    switching = true;
    dir = "asc";
    while (switching) {
        switching = false;
        rows = table.rows;
        for (i = 1; i < (rows.length - 1); i++) {
            shouldSwitch = false;
            x = rows[i].getElementsByTagName("TD")[n];
            y = rows[i + 1].getElementsByTagName("TD")[n];
            // Get <a> element's text
            var xText = x.getElementsByTagName("A")[0] ? x.getElementsByTagName("A")[0].innerText.toLowerCase() : '';
            var yText = y.getElementsByTagName("A")[0] ? y.getElementsByTagName("A")[0].innerText.toLowerCase() : '';
            if (dir == "asc") {
                if (xText == '') continue; // Skip if empty
                if (yText == '') {
                    shouldSwitch = true;
                    break;
                }
                if (xText > yText) {
                    shouldSwitch = true;
                    break;
                }
            } else if (dir == "desc") {
                if (yText == '') continue; // Skip if empty
                if (xText == '') {
                    shouldSwitch = true;
                    break;
                }
                if (xText < yText) {
                    shouldSwitch = true;
                    break;
                }
            }
        }
        if (shouldSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            switchcount++;      
        } else {
            if (switchcount == 0 && dir == "asc") {
                dir = "desc";
                switching = true;
            }
        }
    }
}





function playSound(event) {
	let button = event.target;
	if (button.tagName !== "BUTTON") {
		button = button.parentElement;
	}
	playSound?.currentSound?.pause();
	playSound.currentSound = new Audio("/static/audio/" + button.audioLink);
	playSound.currentSound.play();
}

export function arrayToObject(arr) {
	
	let tab = [];
	let currentSens = -1;
	let tmp = undefined;
	for (let element of arr) {
		if (element[2] !== currentSens) {
			currentSens = element[2];
			if (tmp !== undefined) {
				tab.push(tmp);
			}
			tmp = new Map();
		}
		tmp.set(element[0], {
			text: element[1],
			sens: element[2],
			numeroPage: element[3],
			nomLivre: element[4],
			audioLink: element[5],
		});
	}
	tab.push(tmp);
	return tab;
}

let saveChange = new Map();

export function resetSaveChange() {
	saveChange = new Map();
}

export function mapToArray() {
	let res = [];
	for (let sens of saveChange) {
		let reelSens = sens[0];
		for (let element of sens[1]) {
			res.push(element.concat([reelSens]));
		}
	}
	console.log(res);
	return res;
}

export function sendButtonInit(sendButton) {
	sendButton.addEventListener("click", () => {
	  fetch("/edit", {
		method: "POST",
		headers: {
		  Accept: "application/json",
		  "Content-Type": "application/json",
		},
		body: JSON.stringify(mapToArray()),
	  })
		.then((response) => {
		  if (response.ok) {
			// Fetch réussi
			sendButton.innerHTML = `<i class="fa-solid fa-check" style="color: #ffffff;"></i>`;
			setTimeout(() => {
			  sendButton.innerHTML = `<i class="fa-regular fa-floppy-disk"></i>`;
			}, 1000); // Attendre 1 seconde avant de changer l'icône
		  }
		})
		.catch((error) => {
		  // Gérer les erreurs de fetch
		  console.error(error);
		});
	});
  }
  



export function listernerOnchangeTable(table, editButton) {
	editButton.onclick = (_) => {
		for (let td of document.querySelectorAll("td")) {
			td.contentEditable = true;
			for (let elem of td.children) {
				if (elem.tagName === "BUTTON") {
					elem.remove();
				}
			}
		}
	};
	table.addEventListener("keyup", (event) => {
		if (event.target.tagName.toLowerCase() === "td") {
			let sens = event.target.sens;
			let langue = event.target.langue;
			let text = event.target.innerText;
			if (!saveChange.has(sens)) {
				saveChange.set(sens, new Map());
			}
			saveChange.get(sens).set(langue, text);
		}
	});
}

function selectText(text) {
	if (document.body.createTextRange) {
		// ms
		var range = document.body.createTextRange();
		range.moveToElementText(text);
		range.select();
	} else if (window.getSelection) {
		// moz, opera, webkit
		var selection = window.getSelection();
		var range = document.createRange();
		range.selectNodeContents(text);
		selection.removeAllRanges();
		selection.addRange(range);
	}
}

document.addEventListener("copy", (event) => {
	event.preventDefault();
	if (window.getSelection) {
		let text = window.getSelection().toString();
		navigator.clipboard.writeText(text);
	}
});

document.addEventListener("paste", (event) => {
	event.preventDefault();
	const text = event.clipboardData.getData("text");
	const startCursor = window.getSelection().getRangeAt(0).startOffset;
	const currentText = event.target.innerText;
	event.target.innerText =
		currentText.slice(0, startCursor) +
		text +
		currentText.slice(startCursor, currentText.length);
});

function keyHandler(evt) {
	if (evt.key.toLowerCase() == "enter") {
		evt.preventDefault();
		var cellindex = evt.target.cellIndex;
		var rowindex = evt.target.parentElement.rowIndex;
		selectText(
			document.querySelector("table").children[1].children[rowindex]
				.children[cellindex]
		);
	}
}
