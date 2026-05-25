const fs = require('fs');
let pdf = require('pdf-parse');
let pdfFunc = typeof pdf === 'function' ? pdf : (pdf.default || pdf.pdf);

console.log("pdf exported keys:", Object.keys(pdf));

const pdfPath = 'C:/Users/MacBook Pro/Documents/AOS 100.pdf';
let dataBuffer = fs.readFileSync(pdfPath);

pdfFunc(dataBuffer).then(function (data) {
    fs.writeFileSync('C:/Users/MacBook Pro/Documents/AgentOS/AOS_100.txt', data.text);
    console.log('Done extracting text');
}).catch(e => console.error("Error extracted:", e));
