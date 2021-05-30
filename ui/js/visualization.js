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
    var network = new vis.Network(container, data, options);
}

var yearChange = function(e) {
    buildGraph('' + e.currentTarget.value);
};

document.addEventListener("DOMContentLoaded", async function(event) {
    operators = landlineOperators;
    document.getElementById("year").addEventListener('change', yearChange);
    buildGraph('' + document.getElementById("year").value);
});
