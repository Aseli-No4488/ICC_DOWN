var projectPath = null;

window.onload = function () {
  // Get project path from URL
  const urlParams = new URLSearchParams(window.location.search);
  projectPath = urlParams.get("folder");

  if (projectPath) {
    document.getElementById("projectPath").value = projectPath;
  }
  main(projectPath ?? ".");
};

function handleProjectPathSubmit() {
  projectPath = document.getElementById("projectPath").value;

  if (projectPath) {
    main(projectPath);
  } else {
    alert("Please enter a project path.");
  }
}

function setProgress(text) {
  document.getElementById("progress").innerHTML = text;
}

let network = null;
let data = null;
let project = null;

async function main(projectPath) {
  let url = projectPath + "/project.json";

  if (url.startsWith("http")) {
    url = "https://corsproxy.io/" + url;
  }

  setProgress("Loading project.json...");
  console.time("main");
  fetchWithProgress(url, (loaded, total) => {
    setProgress(`Loading project.json... ${loaded / 1000}KB`);
  })
    // .then((response) => {
    //   setProgress("Parsing project.json...");
    //   return response.json();
    // })
    // .then((_project) => {
    //   // Hash all IDs
    //   const res = _project["rows"].forEach((row) => {
    //     row["id"] = idHash(row["id"]);
    //     row["objects"].forEach((object) => {
    //       object["id"] = idHash(object["id"]);
    //       object["requireds"].forEach((required) => {
    //         required["reqId"] = idHash(required["reqId"]);
    //       });
    //     });
    //   });

    //   return _project;
    // })
    .then((_project) => {
      project = _project;
      setProgress("Extracting data...");

      data = extractData(_project);
      data = dataStyling(data);
      setProgress(
        `Nodes: ${data["nodes"].length}, Edges: ${data["edges"].length}`
      );

      // Set options to default
      document.getElementById("imageSize").value = 6;
      document.getElementById("showRowRelation").checked = true;
      document.getElementById("showHiddenReq").checked = true;
      document.getElementById("groupRow").checked = true;
      // document.getElementById("edgeReduction").value = 80;
      document.getElementById("springLength").value = 150;
      // document.getElementById("margin").value = 5;

      return data;
    })
    .then((data) => visualize(data))
    .then((_network) => {
      network = _network;
      console.timeEnd("main");

      // Optimization by clustering
      // network.clusterByHubsize();
      // network.on("selectNode", function (params) {
      //   if (params.nodes.length == 1) {
      //     network.openCluster(params.nodes[0]);
      //   }
      // });
    })
    .catch((error) => {
      console.warn(error);
      console.timeEnd("main");
      setProgress("프로젝트가 존재하지 않습니다.");
    });
}

function visualize(data) {
  let container = document.getElementById("container");
  let options = {
    interaction: {
      dragNodes: false,
      zoomView: false,
      tooltipDelay: 20,
      hideEdgesOnDrag: true,
    },
    layout: {
      improvedLayout: true,
      // hierarchical: {
      //   direction: "UD",
      //   sortMethod: "directed",
      //   nodeSpacing: 10,
      // },
      randomSeed: 2,
    },
    physics: {
      // stabilization: {
      //   enabled: true,
      //   iterations: 100,
      //   updateInterval: 50,
      // },
      stabilization: false,
      barnesHut: {
        gravitationalConstant: -10000,
        //   springConstant: 0.,
        damping: 0.5,
        springLength: 150,
        avoidOverlap: 0.5,
      },
    },
    interaction: {
      tooltipDelay: 20,
      hideEdgesOnDrag: true,
    },
    nodes: {
      shape: "dot",
      color: {
        border: "#777",
        background: "white",
        highlight: {
          border: "black",
          background: "white",
        },
      },
      margin: 3,
    },
    edges: {
      color: "black",
      smooth: {
        type: "continuous",
      },
      arrows: {
        to: {
          scaleFactor: 0.5,
        },
      },
    },
  };
  console.time("network");
  let network = new vis.Network(container, data, options);
  console.timeEnd("network");
  return network;
}

const imagePathCorrection = (path) => {
  // if it is a relative path
  if (
    !path.includes("http") &&
    !path.includes("data:image") &&
    projectPath &&
    !path.includes("://") &&
    !path.includes("data:")
  ) {
    // merge with project path
    path = projectPath + "/" + path;

    // remove double slashes
    path = path.replace(/([^:]\/)\/+/g, "$1");
  }

  return path;
};

function handleIDRequiredEdges(
  edges,
  from,
  to,
  color,
  highlightColor,
  groups,
  requireIDs
) {
  edges.add({
    from: from,
    to: to,
    arrows: "to",
    dashes: true,
    physics: false,
    color: {
      color: color,
      highlight: highlightColor,
    },
    groups: groups,
  });

  requireIDs.push(to);
}

const extractData = (project) => {
  let nodes = new vis.DataSet();
  let edges = new vis.DataSet();

  console.log(project);

  let groups = project["groups"];
  let rows = project["rows"];
  let requireIDs = [];

  console.log(rows);

  rows.forEach((row, i) => {
    setProgress(`Rows: ${i + 1}/${rows.length}`);

    let x = signedRandom(2500);
    let y = signedRandom(2500);

    let node = {
      id: row["id"],
      label: row["title"],
      title: row["titleText"],
      requireds: row["requireds"],
      groups: "row",
      shape: "box",
      size: 20,
      margin: 15,
      font: {
        color: "#000",
        bold: {
          color: "#000",
          size: 30,
        },
        size: 23,
      },
      x: x,
      y: y,
      physics: false,
    };

    // On click show related objects
    node["chosen"] = {
      node: function (values, id, selected, hovering) {
        handleRow(id);
        return;
      },
    };

    if (row["title"] == "") {
      console.log(row);
      node["color"] = {
        background: "#000",
      };
    }

    if (row["image"]) {
      node["image"] = imagePathCorrection(row["image"]);
      node["shape"] = "image";
    }

    while (true) {
      try {
        nodes.add(node);
        break;
      } catch (error) {
        row["id"] += "-dup";
        node["id"] = row["id"];
      }
    }

    row["requireds"].forEach((required) => {
      if (!required["reqId"]) return;

      if (required["type"] == "id") {
        handleIDRequiredEdges(
          edges,
          row["id"],
          required["reqId"],
          (color = required["required"] ? "#00a6" : "#a006"),
          (highlightColor = required["required"] ? "#00a" : "#a00"),
          "requiredRow",
          requireIDs
        );
      } else {
        console.log("row > excepted require", row["id"], required);
      }
    });

    row["objects"].forEach((object) => {
      let node = {
        id: object["id"],
        label: object["title"],
        shape: "box",
        title: object["titleText"],
        groups: row["id"],
        x: x + signedRandom(50),
        y: y + signedRandom(50),
      };

      // On click show related objects
      node["chosen"] = {
        node: function (values, id, selected, hovering) {
          handleObject(id);
        },
      };

      if (object["image"]) {
        node["image"] = imagePathCorrection(object["image"]);
        node["shape"] = "image";
      }

      while (true) {
        try {
          nodes.add(node);
          break;
        } catch (error) {
          object["id"] += "-dup";
          node["id"] = object["id"];
        }
      }

      edges.add({
        from: row["id"],
        to: object["id"],
        arrows: "to",
        groups: "toRow",
      });

      // requireds
      for (let required of object["requireds"]) {
        // if required is not an id, carefully handle this
        if (required["type"] == "id" && required["reqId"] != "") {
          // Skip if required is already added from row
          if (required["reqId"] in row["requireds"]) continue;

          // Skip for same
          if (required["reqId"] == object["id"]) continue;

          handleIDRequiredEdges(
            edges,
            object["id"],
            required["reqId"],
            (color = required["required"] ? "#00a3" : "#a003"),
            (highlightColor = required["required"] ? "#00a" : "#a00"),
            "requiredObject",
            requireIDs
          );
        } else {
          console.log(
            "object > excepted require",
            object["id"],
            "to",
            required
          );
        }
      }
    });
  });

  // Add missing requireds
  requireIDs.forEach((reqId) => {
    if (!nodes.get(reqId)) {
      nodes.add({
        id: reqId,
        label: reqId,
        shape: "box",
        size: 20,
        margin: 15,
        color: {
          // background: "#a00",
        },
        x: signedRandom(2500),
        y: signedRandom(2500),
      });
    }
  });

  return { nodes: nodes, edges: edges };
};

const dataStyling = (_data) => {
  _data["nodes"].forEach((node) => {
    if (node["label"].includes("color")) {
      node["font"] = {
        color: node["label"].split("color:")[1].split('"')[0],
        bold: true,
        // background: "#000a",
      };
    }

    if (node["label"].includes("font-size")) {
      node["font"] = {
        size: node["label"].split("font-size")[1].split(" ")[0],
      };
    }
    node["label"] = removeHTMLTags(node["label"]);

    node["title"] = node["title"] ? node["title"] : "";
    node["title"] = removeHTMLTags(node["title"]);
  });

  _data = handleImageSizeChange(6, _data, false);
  _data = handleEdgeReduction(80, _data, false);

  return _data;
};

function removeHTMLTags(text) {
  return text ? text.replace(/<[^>]*>?/gm, "") : "";
}

function hasHTMLTags(text) {
  return /<[^>]*>?/gm.test(text);
}

const signedRandom = (max = 1) => {
  return Math.random() * 2 * max - max;
};

let simulation = true;
function handleSimulationButton() {
  // network.addNode({ id: "test", label: "test" });
  console.log("simulation", simulation);
  if (simulation) {
    simulation = false;
    network.stopSimulation();
    document.getElementById("simulationButton").innerHTML =
      "시뮬레이션 시작하기";
  } else {
    simulation = true;
    network.startSimulation();
    document.getElementById("simulationButton").innerHTML = "시뮬레이션 멈추기";
  }
}

function fetchWithProgress(url, updateProgress) {
  return fetch(url).then((response) => {
    if (!response.body) {
      throw new Error("ReadableStream is not supported in this browser.");
    }

    const contentLength = response.headers.get("Content-Length");
    if (!contentLength) {
      console.warn("Content-Length header is not available");
    }

    const total = contentLength ? parseInt(contentLength, 10) : null;
    let loaded = 0;

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let jsonData = "";

    const intervalId = setInterval(() => {
      updateProgress(loaded, total);
    }, 100);

    function read() {
      return reader.read().then(({ done, value }) => {
        if (done) {
          clearInterval(intervalId);
          if (total !== null) updateProgress(total, total); // Ensure full progress is shown
          return JSON.parse(jsonData);
        }
        loaded += value ? value.length : 0;
        jsonData += decoder.decode(value, { stream: true });
        return read();
      });
    }

    return read();
  });
}

async function update(_data) {
  // Get node position before setting new data
  let positions = network.getPositions();

  _data["nodes"].forEach((node) => {
    if (positions[node["id"]]) {
      node["x"] = positions[node["id"]].x;
      node["y"] = positions[node["id"]].y;
    }
  });

  // network.setData(_data);
  // Carefully Update data
  // -- // Update nodes
  let nodes = _data["nodes"];
  let edges = _data["edges"];

  nodes.forEach((node) => {
    if (network.body.nodes[node["id"]]) {
      network.body.nodes[node["id"]].setOptions(node);
    } else {
      network.body.data.nodes.add(node);
    }
  });

  // -- // Update edges
  edges.forEach((edge) => {
    if (network.body.edges[edge["id"]]) {
      network.body.edges[edge["id"]].setOptions(edge);
    } else {
      network.body.data.edges.add(edge);
    }
  });

  // // set camera position
  let cameraPosition = network.getViewPosition();
  let cameraScale = network.getScale();
  network.moveTo({
    position: cameraPosition,
    scale: cameraScale,
  });
}

async function redrawWithPosition(_data) {
  // Get node position before setting new data
  let positions = network.getPositions();

  _data["nodes"].forEach((node) => {
    if (positions[node["id"]]) {
      node["x"] = positions[node["id"]].x;
      node["y"] = positions[node["id"]].y;
    }
  });

  // set camera position
  let cameraPosition = network.getViewPosition();
  let cameraScale = network.getScale();

  //
  network.setData(_data);

  network.moveTo({
    position: cameraPosition,
    scale: cameraScale,
  });
}

function handleImageSizeChange(value, _data = data, redraw = true) {
  console.log("handleImageSizeChange", value);

  let idCount = getEdgeIdCount();

  _data["nodes"].forEach((node) => {
    if (idCount[node["id"]]) {
      node["size"] = Math.log(idCount[node["id"]]) * (value / 2) + value;
    } else {
      node["size"] = value;
    }
  });

  if (redraw) {
    update(_data);
  }

  return _data;
}

function handleShowRowRelation(value, _data = data, redraw = true) {
  console.log("handleShowRowRelation", value);

  _data["edges"].forEach((edge) => {
    if (edge["groups"] == "toRow") {
      edge["hidden"] = !value;
    }
  });

  if (redraw) {
    update(_data);
  }
  return _data;
}

function handleShowHiddenReq(value) {
  console.log("handleShowHiddenReq", value);

  data["edges"].forEach((edge) => {
    if (edge["groups"] == "requiredRow" || edge["groups"] == "requiredObject") {
      edge["hidden"] = !value;
    }
  });

  update(data);
}

function handleGroupRow(value) {
  console.log("handleGroupRow", value);

  // Hide all nodes except rows and children of selected row
  data["nodes"].forEach((node) => {
    // Hide all nodes except rows
    if (node["groups"] == "row") return;

    node["hidden"] = !value;
  });

  redrawWithPosition(data);
}

const autoPhysics = () => {
  return document.getElementById("autoPhysics").checked;
};

let handleRowLog = {};
function handleRow(id) {
  // Skip for too many call

  if (handleRowLog[id]) {
    // Compare time
    let currentTime = new Date().getTime();
    let diff = currentTime - handleRowLog[id];

    if (diff < 500) {
      return;
    } else {
      handleRowLog[id] = new Date().getTime();
    }
  } else {
    handleRowLog[id] = new Date().getTime();
  }

  _handleRow(id);
}

function _handleRow(id) {
  if (document.getElementById("groupRow").checked) {
    console.log("handleRow", "groupRow is checked");
    return;
  }

  console.log("handleRow", id);

  let change = false;

  // Show all connected edges and connected nodes
  data["edges"].forEach((edge) => {
    if (edge["from"] == id || edge["to"] == id) {
      edge["hidden"] = false;

      const f = data["nodes"].get(edge["from"]);
      const t = data["nodes"].get(edge["to"]);

      if (f["hidden"] || t["hidden"]) {
        change = true;
      }

      f["hidden"] = false;
      t["hidden"] = false;

      // f["physics"] = autoPhysics();
      // t["physics"] = autoPhysics();
      // edge["physics"] = autoPhysics();
    } else if (!edge["groups"] == "toRow") {
      edge["physics"] = false;
    }
  });

  if (change) {
    redrawWithPosition(data);
  } else {
    update(data);
  }
}

let handleObjectLog = {};
function handleObject(id) {
  // Skip for too many call

  if (handleObjectLog[id]) {
    // Compare time
    let currentTime = new Date().getTime();
    let diff = currentTime - handleObjectLog[id];

    if (diff < 500) {
      return;
    } else {
      handleObjectLog[id] = new Date().getTime();
    }
  } else {
    handleObjectLog[id] = new Date().getTime();
  }

  _handleObject(id);
}

function _handleObject(id) {
  console.log("handleObject", id);

  let selectedNode = data["nodes"].get(id);

  let change = false;

  // Show all connected edges and connected nodes
  data["edges"].forEach((edge) => {
    if (edge["from"] == id || edge["to"] == id) {
      edge["hidden"] = false;

      const f = data["nodes"].get(edge["from"]);
      const t = data["nodes"].get(edge["to"]);

      if (f["hidden"] || t["hidden"]) {
        change = true;
      }

      f["hidden"] = false;
      t["hidden"] = false;

      f["physics"] = autoPhysics();
      t["physics"] = autoPhysics();
      edge["physics"] = autoPhysics();
    } else if (!edge["groups"] == "toRow") {
      edge["physics"] = false;
    }
  });

  if (change) {
    redrawWithPosition(data);
  } else {
    update(data);
  }
}

function handleEdgeReduction(threshold, _data = data, redraw = true) {
  console.log("handleEdgeReduction", threshold);

  let idCount = getEdgeIdCount();

  // Edge reduction optimization
  _data["edges"].forEach((edge) => {
    if (idCount[edge["to"]] > threshold) {
      edge["hidden"] = true;
    } else {
      edge["hidden"] = false;
    }
  });

  if (redraw) {
    update(_data);
  }
  return _data;
}

function handleSimulationOptionChange() {
  let sprintLengthElement = document.getElementById("springLength");
  // let marginElement = document.getElementById("margin");

  let springLength = sprintLengthElement ? sprintLengthElement.value : 150;
  // let margin = marginElement ? marginElement.value : 5;

  console.log("handleSimulationOptionChange", springLength);

  network.setOptions({
    physics: {
      barnesHut: {
        springLength: Number(springLength),
      },
    },
    nodes: {
      // margin: Number(margin),
      // imagePadding: Number(margin),
    },
  });

  // network.stabilize();
  update(data);
}

function getEdgeIdCount(_data = data) {
  let idCount = {};

  _data["edges"].forEach((edge) => {
    if (idCount[edge["to"]]) {
      idCount[edge["to"]] += 1;
    } else {
      idCount[edge["to"]] = 1;
    }
  });

  return idCount;
}

function idHash(string) {
  let hash = 0;
  if (string.length == 0) return hash;
  for (let i = 0; i < string.length; i++) {
    let char = string.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return Math.abs(hash);
}
