import {
	createTableResult,
	arrayToObject,
	resetSaveChange,
	listernerOnchangeTable,
	sendButtonInit,
} from "./function.js";
const urlParam = new URLSearchParams(window.location.search);
const livre = urlParam.get("livre");
const numPage = parseInt(urlParam.get("page"));
const showBox = urlParam.get("showBox") === "true";
// todo a changé par une valeur prise dans le pdf
const MAX_NUM_PAGE = 274;
resetSaveChange();

let editButton = document.querySelector("#edit");
let sendButton = document.querySelector("#send");
let checkBox = document.querySelector("#showBox");
let selectPage = document.querySelector("#selectPage");
for (let i = 0; i <= MAX_NUM_PAGE; i++) {
	console.log("oui");
	const option = document.createElement("option");
	option.value = i;
	option.innerText = i;
	selectPage.appendChild(option);
}
checkBox.checked = showBox;
let livreBox = livre + "-rectangle";
let livreStart = livre;
if (showBox) {
	livreStart = livreBox;
}
selectPage.value = numPage;
document.querySelector(
	"#pdfViewer"
).src = `static/pdf/${livreStart}.pdf#page=${numPage}`;

function changePage(num) {
	const url = new URL(window.location);
	if (numPage > 1) {
		const newURL = `${url.pathname}?livre=${livre}&page=${num}&showBox=${checkBox.checked}`;
		window.location.href = newURL;
	}
}

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

listernerOnchangeTable(document.querySelector("#table"), editButton);

sendButtonInit(sendButton);

let listeLangue = "";
fetch("/listLangue", {
	method: "POST",
	headers: {
		Accept: "application/json",
		"Content-Type": "application/json",
	},
	body: JSON.stringify({ livre: livre }),
})
	.then((resp) => resp.json())
	.then((json) => {
		listeLangue = json;
	});

fetch("/getPage", {
	method: "POST",
	headers: {
		Accept: "application/json",
		"Content-Type": "application/json",
	},
	body: JSON.stringify({
		livre: livre,
		page: numPage,
	}),
})
	.then((resp) => resp.json())
	.then((json) => {
		createTableResult(
			arrayToObject(json),
			"français",
			listeLangue,
			document.querySelector("#resultTitle"),
			document.querySelector("#resultSearch"),
			false
		);
	});

document.querySelector("#next").onclick = next;
function next() {
	changePage(numPage + 1);
}
document.querySelector("#prev").onclick = prev;
function prev() {
	changePage(numPage - 1);
}
selectPage.onchange = (e) => {
	changePage(e.target.value);
};
