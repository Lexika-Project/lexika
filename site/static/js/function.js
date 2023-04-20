export function createTableResult(
	tab,
	langueBase,
	listeLangue,
	resultTitle,
	resultSearch,
	affichePage
) {
	if (affichePage === undefined) {
		affichePage = true;
	}
	let editButton = document.querySelector("#edit");
	let sendButton = document.querySelector("#send");
	editButton.hidden = false;
	sendButton.hidden = false;
	resultTitle.innerHTML = "";
	let trTitle = document.createElement("tr");
	let th;
	for (let langue of listeLangue) {
		th = document.createElement("th");
		th.innerHTML = langue;
		trTitle.appendChild(th);
	}
	if (affichePage) {
		th = document.createElement("th");
		th.innerHTML = "page";
		trTitle.appendChild(th);
	}
	resultTitle.appendChild(trTitle);
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
					td.innerHTML = `<a class="linkHistory" target="_blank" rel="noopener noreferrer" href="historique?sens=${sens}&langue=${langue}">${
						ligne.get(langue).text
					}</a>`;
					if (
						ligne.get(langue).audioLink !== null &&
						ligne.get(langue).audioLink !== undefined
					) {
						const button = document.createElement("button");
						button.innerHTML = '<i class="fa fa-volume-up"></i>';
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
			if (affichePage) {
				td = document.createElement("td");
				let num = ligne.get(langueBase).numeroPage;
				let livre = ligne.get(langueBase).nomLivre;
				td.innerHTML = `<a class="linkPdf" target="_blank" rel="noopener noreferrer" href="correction-page?livre=${livre}&page=${num}&showBox=false">${num}</a>`;
				tr.appendChild(td);
			}

			resultSearch.appendChild(tr);
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

export function arrayToObject(arr, affichePage) {
	if (affichePage === undefined) {
		affichePage = true;
	}
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
		if (affichePage) {
			tmp.set(element[0], {
				text: element[1],
				sens: element[2],
				numeroPage: element[3],
				nomLivre: element[4],
				audioLink: element[5],
			});
		} else {
			tmp.set(element[0], {
				text: element[1],
				sens: element[2],
			});
		}
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
	return res;
}

export function sendButtonInit(sendButton) {
	sendButton.addEventListener("click", (_) => {
		fetch("/edit", {
			method: "POST",
			headers: {
				Accept: "application/json",
				"Content-Type": "application/json",
			},
			body: JSON.stringify(mapToArray()),
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
