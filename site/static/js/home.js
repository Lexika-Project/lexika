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
const engine = urlParam.get("engine");

let input = document.querySelector("#search");

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
	const newURL = `${url.pathname}?keyword=${keyword}&engine=${engine}&langueBase=${langueBase}&langueTarget=${langueTarget}&page=${num}`;
	newElement.href = newURL;
	div.appendChild(newElement);
}

function createPageCount(total) {
	const nbPage = Math.trunc(total / MAX_SIZE_TABLE);
	if (numPage < nbPage) {
		nextButton.hidden = false;
		nextButton.onclick = (_) => {
			changePage(keyword, engine, langueBase, langueTarget, numPage + 1);
		};
	} else {
		nextButton.hidden = true;
	}
	if (numPage > 1) {
		prevButton.hidden = false;
		prevButton.onclick = (_) => {
			changePage(keyword, engine, langueBase, langueTarget, numPage - 1);
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
				if (json.table.length === 0) {
					// Aucun résultat trouvé
					console.log("Aucun résultat trouvé pour votre recherche.");
					const message = document.createElement('p');
					message.textContent = 'Aucun résultat trouvé pour votre recherche.';
					document.querySelector('body').appendChild(message);
				} else {
					// Résultats trouvés
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

const regexCommands = [
	{ expression: '.', description: "Correspond à n'importe quel caractère sauf un saut de ligne", example: 'a.o → ao, abo, a2o' },
	{ expression: '*', description: 'Répète le caractère précédent zéro ou plusieurs fois', example: 'ab*c → ac, abc, abbc' },
	{ expression: '+', description: 'Répète le caractère précédent une ou plusieurs fois', example: 'ab+c → abc, abbc' },
	{ expression: '?', description: 'Rend le caractère précédent facultatif (0 ou 1 fois)', example: 'ab?c → ac, abc' },
	{ expression: '^', description: 'Correspond au début de la chaîne', example: '^abc → abc, abcdef' },
	{ expression: '$', description: 'Correspond à la fin de la chaîne', example: 'abc$ → abc, defabc' },
	{ expression: '{n}', description: 'Répète le caractère précédent exactement n fois', example: 'a{3} → aaa' },
	{ expression: '{n,}', description: 'Répète le caractère précédent au moins n fois', example: 'a{2,} → aa, aaa' },
	{ expression: '{n,m}', description: 'Répète le caractère précédent entre n et m fois', example: 'a{2,3} → aa, aaa' },
	{ expression: '[abc]', description: 'Correspond à un des caractères entre les crochets', example: 'a[bc] → ab, ac' },
	{ expression: '[^abc]', description: 'Correspond à tout caractère sauf ceux entre les crochets', example: 'a[^bc] → ad, ae' },
	{ expression: '(a|b)', description: "Correspond à l'un des éléments séparés par le symbole |", example: '(ab|cd) → ab, cd' },
	{ expression: '\d', description: 'Correspond à un chiffre (équivalent à [0-9])', example: 'a\d → a0, a1, a9' },
	{ expression: '\D', description: "Correspond à un caractère qui n'est pas un chiffre", example: 'a\D → aa, a%, a-' },
	{ expression: '\w', description: 'Correspond à un caractère alphanumérique ou un tiret bas', example: 'a\w → aa, a1, a_' },
	{ expression: '\W', description: "Correspond à un caractère qui n'est pas alphanumérique", example: 'a\W → a!, a%, a@' },
	{ expression: '\s', description: 'Correspond à un espace, un tab ou un saut de ligne', example: 'a\s → a , a\t, a\n' },
	{ expression: '\S', description: "Correspond à un caractère qui n'est pas un espace", example: 'a\S → aa, a1, a!' },
	// Add more regex expressions, their descriptions, and examples here
];

const regexCommandsContainer = document.getElementById('regex-commands');

function displayRegexCommands() {
	// Create a table element
	const table = document.createElement('table');

	// Create a table header
	const thead = document.createElement('thead');
	const headerRow = document.createElement('tr');
	const headerExpression = document.createElement('th');
	headerExpression.innerText = 'Expression';
	const headerDescription = document.createElement('th');
	headerDescription.innerText = 'Description';
	const headerExample = document.createElement('th');
	headerExample.innerText = 'Exemple';
	headerRow.appendChild(headerExpression);
	headerRow.appendChild(headerDescription);
	headerRow.appendChild(headerExample);
	thead.appendChild(headerRow);
	table.appendChild(thead);

	// Create a table body
	const tbody = document.createElement('tbody');

	for (const command of regexCommands) {
		// Create a table row for each command
		const row = document.createElement('tr');

		// Create table cells for expression, description, and example
		const expressionCell = document.createElement('td');
		expressionCell.innerText = command.expression;
		const descriptionCell = document.createElement('td');
		descriptionCell.innerText = command.description;
		const exampleCell = document.createElement('td');
		exampleCell.innerText = command.example;

		// Append table cells to the row
		row.appendChild(expressionCell);
		row.appendChild(descriptionCell);
		row.appendChild(exampleCell);

		// Append the row to the table body
		tbody.appendChild(row);
	}

	// Create a table footer
	const tfoot = document.createElement('tfoot');

	// Create a footer row
	const footerRow = document.createElement('tr');

	// Create three footer cells
	for (let i = 0; i < 3; i++) {
		const footerCell = document.createElement('th');
		footerRow.appendChild(footerCell);
	}

	// Append the row to the table footer
	tfoot.appendChild(footerRow);

	// Append the table footer to the table
	table.appendChild(tfoot);

	// Append the table body to the table
	table.appendChild(tbody);

	// Clear the previous content and append the table to the container
	regexCommandsContainer.innerHTML = '';
	regexCommandsContainer.appendChild(table);
}

const regexButton = document.getElementById('regex-btn');
regexButton.addEventListener('click', () => {
	if (regexCommandsContainer.style.display === 'none') {
		regexCommandsContainer.style.display = 'block';
		displayRegexCommands();
	} else {
		regexCommandsContainer.style.display = 'none';
	}
});
