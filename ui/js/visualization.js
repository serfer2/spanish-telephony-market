const bigNetworkNodesQuantity = 100;
var operators = mobileOperators;
var dataset = mobileData;
var opsData = null;
var filterYear = new Date().getFullYear();
var network = null;

function opIsSmaller(a, b) {
    if ( a.volume < b.volume ){
        return 1;
    }
    if ( a.volume > b.volume ){
        return -1;
    }
    return 0;
}

function calcMass(l) {
    var m = 2.5;
    if(l > 30 && l < bigNetworkNodesQuantity) {
        m = 1.5;
    }
    return m;
}

function operatorsStats(data) {
    // [{"id":"6","volume":20000,"links":["0"]}, ...]
    let min = data[0].volume;
    let max = data[0].volume;
    let total = 0;
    for (let i in data) {
        total += data[i].volume;
        if (data[i].volume < min) {
            min = data[i].volume;
        }
        if (data[i].volume > max) {
            max = data[i].volume;
        }
    }
    return { 'min': min, 'max': max, 'total': total};
}

function operatorSize(volume, stats) {
    // volume:  <int>,   step:  <int>
    let size = (volume - stats.min) / (stats.max - stats.min); // [0.0, 1.0]

    return parseInt(size * 12);
}

function buildGraph() {
    const stats = operatorsStats(opsData);
    if (network != null) {
        network.destroy();
    }
    var nodesData = [{
        id: "0",
        label: "ER",
        title: `Entidad Reguladora\nDate added:\t1998\nDistributed lines :\t${stats.total.toLocaleString()}`,
        color: { background: '#6f42c1', },
        font: { color: '#ffffff', },
        borderWidth: 2,
        margin: 6,
    },];
    var edgesData = [];
    const nodesQuantity = opsData.length;
    const isBigNetwork = nodesQuantity >= bigNetworkNodesQuantity;

    for(let index in opsData) {
        let op = opsData[index];
        // [ { id: 1, label: "Node 1" }, { id: 2, label: "Node 2" }, ... ]
        let size = operatorSize(op.volume, stats);
        let nodeData = {
            id: op.id,
            label: operators[op.id].name,
            margin: 2 * (1 + size),
            title: `${operators[op.id].name}\nDate added:\t${operators[op.id].date_added}\nTotal lines:\t${op.volume.toLocaleString()}`,
            value: op.volume,
        }
        if (!isBigNetwork) {
            nodeData.mass = calcMass(nodesQuantity)
        }
        nodesData.push(nodeData);
        for (let _id in op.links) {
            // [ { from: 1, to: 3 }, { from: 1, to: 2 }, ... ]
            edgesData.push({ 'from': _id, 'to': op.id });
        }
    }

    var edges = new vis.DataSet(edgesData);
    var nodes = new vis.DataSet(nodesData);

    // Network graph
    var container = document.getElementById("graph");
    var data = { nodes: nodes, edges: edges };
    var options = {
        autoResize: true,
        height: '600px',
        width: '1200px',
        nodes: {
          shape: "box",
          chosen: {
                node: function(values, id, selected, hovering) {
                    values.borderColor = '#6f42c1';
                    values.borderWidth = 2;
                    values.color = '#f1f9b1';
                },
                label: function(values, id, selected, hovering) {
                    values.color = '#000';
                }
          },
        },
        edges: {
          color: { inherit: true },
          width: 0.15,
          smooth: {
            type: "continuous",
          },
        },
        interaction: {
          hideEdgesOnDrag: true,
          tooltipDelay: 200,
        },
    };
    if (isBigNetwork) {
        document.getElementById("loading").style.display = 'block';
        options.layout = {
            improvedLayout: false,
        };
    }

    network = new vis.Network(container, data, options);
    network.once("afterDrawing", function () {
        if (isBigNetwork) {
            document.getElementById("loading").style.display = 'none';
        }
    });
    network.on("click", function (params) {
        var _id = params.nodes[0];
        if (_id == undefined || _id == '0') {
            return;
        }
        selectCompany(_id);
    });
}

var yearInput = function(e) {
    document.getElementById('yearValue').innerText = '' + e.currentTarget.value;
};

function buildSelectorFilter() {
    var $f = $('#filter');
    $f.empty();
    const text = 'Search (ordered by size)';
    $f.append(
        $('<option></option>').attr("data-tokens", "0").attr("disabled", true).attr("selected", true).text(text)
    );
    $.each(opsData, function(i, op) {
        $f.append($("<option></option>").attr("data-tokens", op.id).attr("value", op.id).text(operators[op.id].name));
    });
    $f.selectpicker({liveSearch: true});
    $f.selectpicker('refresh');
    $f.selectpicker('render');
}

function applyFilters() {
    const year = parseInt(document.getElementById('year').value);
    const limit = parseInt(document.getElementById('limit').value);
    dataset[year].operators.sort(opIsSmaller)
    opsData = dataset[year].operators.slice(0, limit);
    buildSelectorFilter();
    buildGraph();
}

var datasetChange = function(e) {
    $( "#dataset_mobile" ).removeClass('active');
    $( "#dataset_landline" ).removeClass('active');
    var obj = $( e.target );
    if (obj.attr('id') == "dataset_landline") {
        dataset = landlineData;
        operators = landlineOperators;
        $( "#dataset_landline" ).addClass('active');
    } else {
        dataset = mobileData;
        operators = mobileOperators;
        $( "#dataset_mobile" ).addClass('active');
    }
    applyFilters();
}

function selectCompany(_id) {
    var volume = 0;
    for (let i in opsData) {
        if (opsData[i].id == _id) {
            volume = opsData[i].volume;
            break;
        }
    }
    network.selectNodes([_id,], true);
        var info = `  ${operators[_id].name} (added: ${operators[_id].date_added})`;
        if (volume != 0) {
            info += `. Total lines: ${volume.toLocaleString()}`;
        }
        $("#filteredCompany").text(info);
}

document.addEventListener("DOMContentLoaded", async function(event) {
    document.getElementById("year").addEventListener('change', applyFilters);
    document.getElementById("year").addEventListener('input', yearInput);
    document.getElementById("limit").addEventListener('change', applyFilters);
    let year = '' + document.getElementById("year").value;
    document.getElementById('yearValue').innerText = year;
    // document.getElementById("dataset_landline").addEventListener('click', datasetChange);
    // document.getElementById("dataset_mobile").addEventListener('click', datasetChange);
    if (dataset == landlineData) {
        $( "#dataset_landline" ).addClass('active');
    } else {
        $( "#dataset_mobile" ).addClass('active');
    }
    $( "#dataset_landline" ).click(datasetChange);
    $( "#dataset_mobile" ).click(datasetChange);
    $( "#filter" ).change(function (e){
        selectCompany($(this).val())
    });
    applyFilters();
    
});
