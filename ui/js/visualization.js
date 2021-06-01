var operators = null;
var dataset = landlineData;
var filterYear = new Date().getFullYear(); 


function buildGraph(year) {
    var nodesData = [ { id: "0", label: "ER" }, ];
    var edgesData = [];

    for(let index in dataset[year].operators) {
        let op = dataset[year].operators[index];
        // [ { id: 1, label: "Node 1" }, { id: 2, label: "Node 2" }, ... ]
        nodesData.push({ id: op.id, label: operators[op.id].name });
        for (let _id in op.links) {
            // [ { from: 1, to: 3 }, { from: 1, to: 2 }, ... ]
            edgesData.push({ 'from': op.id, 'to': _id });
        }
    }

    var edges = new vis.DataSet(edgesData);
    var nodes = new vis.DataSet(nodesData);

    // Network graph
    var container = document.getElementById("graph");
    var data = { nodes: nodes, edges: edges };
    var options = {};
    console.log('--- Nodos: ' + nodesData.length);
    if (nodesData.length > 25) {
        options.layout = {
            improvedLayout: false,
        };
    }
    var network = new vis.Network(container, data, options);
}

var yearChange = function(e) {
    buildGraph('' + e.currentTarget.value);
};
var yearInput = function(e) {
    document.getElementById('yearValue').innerText = '' + e.currentTarget.value;
};

var datasetChange = function(e) {
    document.getElementById('dataset_landline').classList.remove('active');
    document.getElementById('dataset_mobile').classList.remove('active');
    e.currentTarget.classList.add('active');
    dataset = (dataset == landlineData) ? mobileData: landlineData;
    buildGraph('' + document.getElementById("year").value);
}

document.addEventListener("DOMContentLoaded", async function(event) {
    operators = landlineOperators;
    document.getElementById("year").addEventListener('change', yearChange);
    document.getElementById("year").addEventListener('input', yearInput);
    let year = '' + document.getElementById("year").value;
    document.getElementById('yearValue').innerText = year;
    document.getElementById("dataset_landline").addEventListener('click', datasetChange);
    document.getElementById("dataset_mobile").addEventListener('click', datasetChange);
    if (dataset == landlineData) {
        document.getElementById('dataset_landline').classList.add('active');
    } else {
        document.getElementById('dataset_mobile').classList.add('active');
    }
    buildGraph(year);
});
