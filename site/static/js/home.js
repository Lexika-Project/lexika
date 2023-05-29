import {
	createTableResult,
	arrayToObject,
	resetSaveChange,
	listernerOnchangeTable,
	sendButtonInit,
} from "./function.js";

const MAX_SIZE_TABLE = 25;

const urlParam = new URLSearchParams(window.location.search);
const keyword = urlParam.get("keyword");
const langueBase = urlParam.get("langueBase");
const langueTarget = urlParam.get("langueTarget");
const numPage = parseInt(urlParam.get("page"));

let input = document.querySelector("#search");
let lastJsonResponse;
let listeLangues = [];
let resultSelect = document.querySelector("#resultSelect");
let baseSelect = document.querySelector("#baseSelect");


let engineSelectElem;
let engineSelect;

const urlParamEngine = urlParam.get("engine");
if (urlParamEngine) {
  // Vérifier la valeur de "engine" dans l'URL
  engineSelectElem = document.querySelector(`input[name="radio"][value="${urlParamEngine}"]`);
}

if (engineSelectElem) {
  // Si le bouton radio correspondant à "engine" existe, le sélectionner
  engineSelectElem.checked = true;
  engineSelect = engineSelectElem.value;
} else {
  // Si aucun bouton radio correspondant n'est trouvé, sélectionner le bouton radio "tsquery" par défaut
  document.querySelector('#tsquery').checked = true;
  engineSelect = 'tsquery';
}

document.querySelectorAll('input[name="radio"]').forEach((radio) => {
  radio.addEventListener('change', function() {
    engineSelect = this.value;
    // Stocker la valeur de engineSelect dans le localStorage
    localStorage.setItem('engineSelect', engineSelect);
  });
});


main();

function listeDesLangue() {
	if (resultSelect.value === "all") {
		return [baseSelect.value].concat(
			listeLangues.filter((e) => e !== baseSelect.value)
		);
	} else {
		return [baseSelect.value, resultSelect.value];
	}
}

let editButton = document.querySelector("#edit");
let sendButton = document.querySelector("#send");
let nextButton = document.querySelector("#next");
let prevButton = document.querySelector("#prev");

function changePage(keyword, engine, langueBase, langueTarget, numPage) {
	const url = new URL(window.location);
	const newURL = `${url.pathname}?keyword=${keyword}&engine=${engine}&langueBase=${langueBase}&langueTarget=${langueTarget}&page=${numPage}`;
	window.location.href = newURL;
}

function createNum(div, num) {
	const newElement = document.createElement("a");
	newElement.classList.add("pageNumber");

	newElement.innerText = num;
	const url = new URL(window.location);
	const newURL = `${url.pathname}?keyword=${keyword}&engine=${engineSelect}&langueBase=${langueBase}&langueTarget=${langueTarget}&page=${num}`;
	newElement.href = newURL;
	div.appendChild(newElement);
}

function createPageCount(total) {
	const nbPage = Math.trunc(total / MAX_SIZE_TABLE);
	if (numPage < nbPage) {
		nextButton.hidden = false;
		nextButton.onclick = (_) => {
			changePage(keyword, engineSelect, langueBase, langueTarget, numPage + 1);
		};
	} else {
		nextButton.hidden = true;
	}
	if (numPage > 1) {
		prevButton.hidden = false;
		prevButton.onclick = (_) => {
			changePage(keyword, engineSelect, langueBase, langueTarget, numPage - 1);
		};
	} else {
		prevButton.hidden = true;
	}
	const div = document.querySelector("#pageDisplay");

	if (numPage > 3) {
		createNum(div, "1");
		div.innerHTML += "...";
	}
	if (numPage > 2) {
		createNum(div, numPage - 2);
	}
	if (numPage - 1 > 0) {
		createNum(div, numPage - 1);
	}
	const span = document.createElement("span");
	span.classList.add("currentPage");
	span.innerText = numPage;
	div.appendChild(span);
	if (numPage + 1 < nbPage + 1) {
		createNum(div, numPage + 1);
	}
	if (numPage + 2 < nbPage + 1) {
		createNum(div, numPage + 2);
	}
	if (numPage < nbPage - 3) {
		div.innerHTML += "...";
		createNum(div, nbPage);
	}
}

async function search(keyword, engine, langueBase, langueResult, page) {
	const offset = (page - 1) * 25;
	resetSaveChange();
	if (keyword !== "") {
		const loader = document.querySelector(".typewriter");
		loader.removeAttribute('hidden');

		await fetch("/search", {
			method: "POST",
			headers: {
				Accept: "application/json",
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				keyword: keyword.toLowerCase(),
				engine: engine,
				langueBase: langueBase,
				langueResult: langueResult,
				offset: offset,
			}),
		})
		.then((resp) => resp.json())
		.then((json) => {
			if (json.verif === "ok") {
				lastJsonResponse = json;
				if (json.table.length === 0) {
					// Aucun résultat trouvé
					console.log("Aucun résultat trouvé pour votre recherche.");
					const message = document.createElement('p');
					message.textContent = 'Aucun résultat trouvé pour votre recherche.';
					document.querySelector('body').appendChild(message);
				} else {
					// Résultats trouvés.
					console.log(json.table);
					createPageCount(json.count);
					createTableResult(
						arrayToObject(json.table),
						langueBase,
						listeDesLangue(),
						document.querySelector("#resultTitle"),
						document.querySelector("#resultSearch"),
						true
					);
				}
			} else {
				console.log("Erreur de la base de données");
			}
		})
		.finally(() => {
			loader.setAttribute('hidden', '');
		});
	}
}

document.querySelector("#searchButton").addEventListener("click", (_) => {
	console.log(engineSelect);
	changePage(
		input.value,
		engineSelect,
		baseSelect.value,
		resultSelect.value,
		1
	);
});

document.querySelector("#search").addEventListener("keypress", (event) => {
	if (event.key.toLowerCase() === "enter") {
		changePage(
			input.value,
			engineSelect,
			baseSelect.value,
			resultSelect.value,
			1
		);
	}
});

async function main() {
	engineSelect = localStorage.getItem('engineSelect');
	let resp = await fetch("/listLangue", {
		method: "POST",
		headers: {
			Accept: "application/json",
			"Content-Type": "application/json",
		},
		body: JSON.stringify({ livre: "all" }),
	});

	listeLangues = await resp.json();

	for (let langue of listeLangues) {
		let tmp = document.createElement("option");
		tmp.innerText = langue;
		baseSelect.appendChild(tmp);
	}

	let tmp = document.createElement("option");
	resultSelect.appendChild(tmp);
	tmp.innerText = "Toutes les langues";
	tmp.value = "all";

	for (let langue of listeLangues) {
		let tmp = document.createElement("option");
		tmp.innerText = langue;
		resultSelect.appendChild(tmp);
	}

	if (keyword !== null && !isNaN(numPage) && langueBase !== null && langueTarget !== null) {
		input.value = keyword;
		baseSelect.value = langueBase;
		resultSelect.value = langueTarget;
		resultSelect.onchange = (_) => {
			changePage(keyword, engineSelect, langueBase, resultSelect.value, numPage);
		};

		baseSelect.onchange = (_) => {
			changePage(keyword, engineSelect, baseSelect.value, langueTarget, numPage);
		};

		await search(keyword, engineSelect, langueBase, langueTarget, numPage);
	}

	resetSaveChange();
	listernerOnchangeTable(document.querySelector("#table"), editButton);

	sendButtonInit(sendButton);
}

const regexButton = document.getElementById('regex-btn');
const regexDiv = document.getElementById('regex-div');

// Utilisez cette fonction pour afficher la table avec une transition
function showTable() {
    regexDiv.style.display = 'flex';
    // Nous devons donner au navigateur le temps de rendre l'élément avant de changer son opacité
    // sinon il n'y aura pas de transition.
    setTimeout(() => {
        regexDiv.style.opacity = '1';
    }, 50); // 50ms est suffisant dans la plupart des cas
}

// Utilisez cette fonction pour masquer la table avec une transition
function hideTable() {
    regexDiv.style.opacity = '0';
    // Nous devons attendre que la transition de l'opacité soit terminée avant de masquer l'élément
    // sinon nous ne verrons pas la transition.
    setTimeout(() => {
        regexDiv.style.display = 'none';
    }, 300); // Le délai doit être le même que la durée de la transition CSS
}

regexButton.addEventListener('click', () => {
  if (regexDiv.style.opacity == 0) {
    showTable();
  } else {
    hideTable();
  }
});


function JSONtoCSV(json) {
    const replacer = (key, value) => value === null ? '' : value;
    const header = Object.keys(json[0]);
    let csv = json.map(row => header.map(fieldName => JSON.stringify(row[fieldName], replacer)).join(','));
    csv.unshift(header.join(','));
    return csv.join('\r\n');
}


document.querySelector('#download-csv').addEventListener('click', function() {
	// Vérifier s'il y a une réponse JSON à convertir en CSV
	if (lastJsonResponse) {
		// Convertir le JSON en CSV
		let csv = JSONtoCSV(lastJsonResponse.table);
		
		// Créer un Blob à partir du CSV
		let csvBlob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
		
		// Créer un lien pour télécharger le Blob
		let csvURL = URL.createObjectURL(csvBlob);
		let tempLink = document.createElement('a');
		tempLink.href = csvURL;
		tempLink.setAttribute('download', 'data.csv');
		tempLink.click();
	}
});