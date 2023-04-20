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
let engineSelect = document.querySelector("#engineSelect");
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
			.then((resp) => {
				return resp.json();
			})
			.then((json) => {
				if (json.verif === "ok") {
					createPageCount(json.count);
					createTableResult(
						arrayToObject(json.table),
						langueBase,
						listeDesLangue(),
						document.querySelector("#resultTitle"),
						document.querySelector("#resultSearch")
					);
				} else {
					console.log("Error database");
				}
			});
	}
}
document.querySelector("#searchButton").addEventListener("click", (_) => {
	changePage(
		input.value,
		engineSelect.value,
		baseSelect.value,
		resultSelect.value,
		1
	);
});
document.querySelector("#search").addEventListener("keypress", (event) => {
	if (event.key.toLowerCase() === "enter") {
		changePage(
			input.value,
			engineSelect.value,
			baseSelect.value,
			resultSelect.value,
			1
		);
	}
});

async function main() {
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
	if (
		keyword !== null &&
		numPage !== NaN &&
		langueBase !== null &&
		langueTarget !== null
	) {
		input.value = keyword;
		baseSelect.value = langueBase;
		engineSelect.value = engine;
		resultSelect.value = langueTarget;
		resultSelect.onchange = (_) => {
			changePage(
				keyword,
				engine,
				langueBase,
				resultSelect.value,
				numPage
			);
		};
		engineSelect.onchange = (_) => {
			changePage(
				keyword,
				engineSelect.value,
				langueBase,
				langueTarget,
				numPage
			);
		};
		baseSelect.onchange = (_) => {
			changePage(
				keyword,
				engine,
				baseSelect.value,
				langueTarget,
				numPage
			);
		};
		await search(keyword, engine, langueBase, langueTarget, numPage);
	}

	resetSaveChange();
	listernerOnchangeTable(document.querySelector("#table"), editButton);

	sendButtonInit(sendButton);
}
