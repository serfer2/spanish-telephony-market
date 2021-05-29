var operators = null;
var dataset = landlineData;
var filterYear = new Date().getFullYear(); 


function buildGraph(year) {
    year = '' + year;
    console.log(year);

    var nodesData = [ { id: "0", label: "ER" }, ];
    var edgesData = [];

    console.log(dataset[year].operators);
    for(let index in dataset[year].operators) {
        let op = dataset[year].operators[index];
        // [ { id: 1, label: "Node 1" }, { id: 2, label: "Node 2" }, ... ]
        console.log('' + op.id + ' ' + operators[op.id].date_added + ' ' + operators[op.id].name);
        nodesData.push({ id: op.id, label: operators[op.id].name });
        // [ { from: 1, to: 3 }, { from: 1, to: 2 }, ... ]
        for (let _id in op.links) {
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


document.addEventListener("DOMContentLoaded", async function(event) {
    operators = landlineOperators;
    console.log(operators);
    buildGraph('1999');
});
