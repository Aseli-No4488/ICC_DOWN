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

let network = null;
let data = null;

function main(projectPath) {
  const url = projectPath + "/project.json";

  console.time("main");
  fetch("https://corsproxy.io/" + url, {
    // method: "GET",
    // headers: {
    //   "Content-Type": "*",
    //   Accept: "*",
    // },
    // mode: "cors",
  })
    .then((response) => {
      console.log(response);
      return response.json();
    })
    .then((project) => {
      data = extractData(project);
      dataStyling(data);
      document.getElementById(
        "progress"
      ).innerHTML = `Nodes: ${data["nodes"].length}, Edges: ${data["edges"].length}`;
      return data;
    })
    .then((data) => visualize(data))
    .then((_network) => {
      network = _network;
      console.timeEnd("main");

      // network.clusterByHubsize();
      // network.on("selectNode", function (params) {
      //   if (params.nodes.length == 1) {
      //     network.openCluster(params.nodes[0]);
      //   }
      // });
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
        gravitationalConstant: -1000,
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

const extractData = (project) => {
  const progress = document.getElementById("progress");
  let nodes = new vis.DataSet();
  let edges = new vis.DataSet();

  console.log(project);

  let groups = project["groups"];
  let rows = project["rows"];

  console.log(rows);

  // for (let i = 0; i < rows.length - 0; i++) {
  rows.forEach((row, i) => {
    // const row = rows[i];
    progress.innerHTML = `Rows: ${i + 1}/${rows.length}`;

    let x = signedRandom(2500);
    let y = signedRandom(2500);

    row["id"] += "R";

    let node = {
      id: row["id"],
      label: row["title"],
      title: row["titleText"],
      requireds: row["requireds"],
      groups: row["id"],
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
    nodes.add(node);

    // for (let object of row["objects"]) {
    row["objects"].forEach((object) => {
      let node = {
        id: object["id"],
        label: object["title"],
        shape: "box",
        title: object["titleText"],
        groups: row["id"],
        // hidden: true,
        x: x + signedRandom(50),
        y: y + signedRandom(50),
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
      });

      // requireds
      for (let required of row["requireds"]) {
        if (
          required["required"] &&
          required["type"] == "id" &&
          required["reqId"] !== object["id"]
        ) {
          edges.add({
            from: object["id"],
            to: required["reqId"],
            // arrows: "to",
            dashes: true,
            physics: false,
            color: {
              color: "#0003",
            },
            groups: "required",
          });
        }
      }
    });
  });
  return { nodes: nodes, edges: edges };
};

const dataStyling = (data) => {
  data["nodes"].forEach((node) => {
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

  let idCount = {};
  data["edges"].forEach((edge) => {
    if (idCount[edge["to"]]) {
      idCount[edge["to"]] += 1;
    } else {
      idCount[edge["to"]] = 1;
    }
  });
  data["nodes"].forEach((node) => {
    if (idCount[node["id"]]) {
      node["size"] = Math.log(idCount[node["id"]]) * 6 + 13;
    } else {
      node["size"] = 13;
    }
  });

  // Edge reduction optimization
  // data["edges"].forEach((edge) => {
  //   if (idCount[edge["to"]] > 80) {
  //     edge["hidden"] = true;
  //   } else {
  //     edge["hidden"] = false;
  //   }
  // });
  return data;
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
