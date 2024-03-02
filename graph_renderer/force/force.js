
// Copyright 2023 Two Six Technologies
// 
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// 
//     http://www.apache.org/licenses/LICENSE-2.0
// 
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// 

var node_default_radius = 15;

var rect = visualViewport;
var x_center = rect.width/2;
var y_center = rect.height/2;

var svg = d3.select("div#container")
    .append("svg")
    .attr("width", rect.width)
    .attr("height", rect.height)
    .attr("preserveAspectRatio", "xMinYMin meet")
    .classed("svg-content", true);

addEventListener("resize",
                 (_) => {
                     svg.attr("width", visualViewport.width)
                         .attr("height", visualViewport.height)
                         .attr("preserveAspectRatio", "xMinYMin meet")
                 })

// https://bl.ocks.org/d3noob/a22c42db65eb00d4e369
var div = d3.select("body").append("div")
    .attr("class", "tooltip")
    .style("opacity", 0);

//var color = d3.scaleOrdinal(d3.schemeCategory20);

refresh_data();

//console.log(refreshTime);
//console.log(linkAttr);
//console.log(withLabels);
//console.log(collapseLinks);

d3.interval(refresh_data, refreshTime);

saved_graph = ""

function refresh_data() {
    d3.json("force/graph.json").then(function(graphObj) {

      new_graph = JSON.stringify(graphObj);
      if (new_graph == saved_graph) {
          return;
      }

      //console.log(graphObj);

      saved_graph = new_graph;
      svg.selectAll("g").remove();

      graph_nodes = graphObj.nodes;
      all_links = graphObj.links;

      var num_nodes = graph_nodes.length;
      var node_radius = node_default_radius / Math.log(num_nodes);

      // Assign an linknum index for each link between the same set of nodes
      all_links.sort(function(a,b) {
          if (a.source > b.source) {return 1;}
          else if (a.source < b.source) {return -1;}
          else {
              if (a.target > b.target) {return 1;}
              if (a.target < b.target) {return -1;}
              else {return 0;}
          }
      });
      for (var i=0; i<all_links.length; i++) {
          if (i != 0 &&
              all_links[i].source == all_links[i-1].source &&
              all_links[i].target == all_links[i-1].target) {
            all_links[i].linknum = all_links[i-1].linknum + 1;
          }
          else {all_links[i].linknum = 1;};
          peers = [all_links[i].source, all_links[i].target];
          all_links[i].trace = ""
          var traced = ""
	  if (all_links[i].traceId == traceMessage) {
              traced = "trace"
          }
          if (traceMessage2 != "" && all_links[i].traceId == traceMessage2) {
                  traced = "trace2"
          }
          if (traceMessage3 != "" && all_links[i].traceId == traceMessage3) {
                  traced = "trace3"
	  }
          all_links[i].trace = traced
          if (String(collapseLinks) == "true" && all_links[i].traceId != traceMessage) {
              // Don't differentiate on the basis of directionality unless this is a trace link
              peers = peers.sort();
          }
          all_links[i].peers = peers.join("-");
      };

      // Collapse links
      if (String(collapseLinks) == "true") {
          var linksByPeers = d3.rollup(all_links,
               function(g) {
                   return {
                       // Construct lists with unique elements
                       "channelGid": [...new Set(g.map(function(d) { return d.channelGid; }).flat())].filter((str) => str !== '').join(","),
                       "linkId": [...new Set(g.map(function(d) { return d.linkId; }).flat())].filter((str) => str !== '').join(","),
                       "linkType": [...new Set(g.map(function(d) { return d.linkType; }).flat())].filter((str) => str !== '').join(","),
                       "linkAddress": [...new Set(g.map(function(d) { return d.linkAddress; }).flat())].filter((str) => str !== '').join(","),
                       "connType": [...new Set(g.map(function(d) { return d.connType; }).flat())].filter((str) => str !== '').join(","),
                       "personas": [...new Set(g.map(function(d) { return d.personas; }).flat())].filter((str) => str !== '').join(","),
                       "trace": [...new Set(g.map(function(d) { return d.trace; }).flat())].filter((str) => str !== '').join(","),
                       "conn_in": d3.sum(g.map(function(d) { return d.conn_in; })),
                       "conn_out": d3.sum(g.map(function(d) { return d.conn_out; })),
                       "source": g[0].source,
                       "target": g[0].target,
                       "linknum": 1,
                   }
               },
               d => d.peers);

          collapsed_links = Array.from(linksByPeers.values());

          graph_links = collapsed_links;
      } else {
          graph_links = all_links;
      }

      var edge_sect = svg.append("g");

      var edgepaths = edge_sect
          .selectAll(".edgepath")
          .data(graph_links)
          .enter()
          .append('path')
          .attr('id', function(d, i) {return 'edgepath'+i})
          .attr('class', function(d, i) {
                  if (String(traceMessage) != "") {
                      if (d.trace) {
                          if (d.trace.split(',').length > 1) {
                              return "multitrace links";
                          }
                          return d.trace + " links";
		      } else {
                            return "transparent links";
	              }
                  } else if (String(collapseLinks) == "true") {
                      return "links";
                  } else if (d.connType) {
                      return d.connType + " links";
                  } else {
                      return "invisible links";
                  }
          })
          .attr('marker-end', function(d, i) {
                  if (String(traceMessage) != "") {
                      if (d.trace) {
                          return 'url(#arrowhead)';
		      } else if (String(collapseLinks) == "true") {
                          return '';
                      } else {
                          return 'url(#noarrowhead)';
	              }
                  } else if (String(collapseLinks) == "true") {
                      return '';
                  } else {
                      return 'url(#arrowhead)';
                  }
          })
          .style('fill', 'none')
          .on("mouseover", function(event, d) {
              div.transition()
                  .duration(200)
                  .style("opacity", .9);
              if (d[linkAttr]) {
                  div.html(d[linkAttr].toString().replaceAll(",", "<br/>"))
                      .style("left", (event.pageX) + "px")
                      .style("top", (event.pageY - 28) + "px");
	      }
          })
          .on("mouseout", function(d) {
            div.transition()
                .duration(500)
                .style("opacity", 0);
          });


      if (String(withLabels) == "true") {
          var edgelabels = edge_sect
              .selectAll(".edgelabel")
              .data(graph_links)
              .enter()
              .append('text')
              .attr('class', "edgelabel")
              .attr('dx', 80)
              .attr('dy', 0)
              .attr('font-size', 10)
              .attr('id', function(d, i) {return 'edgelabel'+i});

          edgelabels.append('textPath')
              .attr('href',function(d,i) {return '#edgepath'+i})
              .text(function(d,i){return d[linkAttr]});
      } else {
          edge_sect
              .selectAll(".edgelabel")
              .remove();
      }

      svg.selectAll("defs").remove();

      svg.append('defs').append('marker')
          .attr('id', 'arrowhead')
          .attr("class", "arrowstyle")
          .attr('viewBox', '0 -5 10 10')
          .attr('refX', 25)
          .attr('refY', 0)
          .attr('orient', 'auto')
          .attr('markerWidth', 3)
          .attr('markerHeight', 3)
          .attr('overflow', 'visible')
          .append('svg:path')
          .attr('d', 'M 0,-5 L 10,0 L 0,5');

      svg.append('defs').append('marker')
          .attr('id', 'noarrowhead')
          .attr("class", "noarrowstyle")
          .attr('viewBox', '0 -5 10 10')
          .attr('refX', 25)
          .attr('refY', 0)
          .attr('orient', 'auto')
          .attr('markerWidth', 3)
          .attr('markerHeight', 3)
          .attr('overflow', 'visible')
          .append('svg:path')
          .attr('d', 'M 0,-5 L 10,0 L 0,5');

      var nodeObjs = svg.append("g")
          .attr("class", "nodes")
          .selectAll("g")
          .data(graph_nodes)
          .enter().append("g")

      var circles = nodeObjs.append("circle")
          .attr("class", "node-circle")
          .attr("id", function(d) {
              return d.id;
          })
          .attr("r", node_radius);

      var nodelabels = nodeObjs.append("text")
          .text(function(d) {
            return d.id;
          })
          .attr('x', node_radius)
          .attr('y', 3);

      d3.selectAll(".node-circle[id^='race-server']")
          .attr("class", "node-server");

      d3.selectAll(".node-circle[id^='race-client']")
          .attr("class", "node-client");


      ///////////////////////////////////////////////////////////
      // Force-directed simulation
      ///////////////////////////////////////////////////////////

      function dragstarted(event, d) {
          if (!event.active) simulation.alphaTarget(0.1).restart();
          d.fx = d.x;
          d.fy = d.y;
      }

      function dragged(event, d) {
          d.fx = event.x;
          d.fy = event.y;
      }

      function dragended(event, d) {
          if (!event.active) simulation.alphaTarget(0);
      }

      function resizeGraph() {
          var minX = d3.min(graph_nodes, function(d) {
              return d.x;
          });
          var minY = d3.min(graph_nodes, function(d) {
              return d.y;
          });
          var maxX = d3.max(graph_nodes, function(d) {
              return d.x;
          });
          var maxY = d3.max(graph_nodes, function(d) {
              return d.y;
          });
          var v_width = maxX-minX;
          var v_height = maxY-minY;
          const viewbox = `${minX-100} ${minY-100} ${v_width+200} ${v_height+200}`;
          svg.attr("viewBox", viewbox);
      };

      function ticked() {
          nodeObjs
              .attr("transform", function(d) {
		      resizeGraph();
		      return "translate(" + d.x + "," + d.y + ")";
              });

          edgepaths.attr('d', function(d) {
              //var dx = d.target.x - d.source.x,
              //dy = d.target.y - d.source.y,
              if (String(collapseLinks) == "true") {
                  return 'M '+d.source.x+' '+d.source.y+' L '+ d.target.x +' '+d.target.y;
              } else {
                  dr = 1000/Math.sqrt(d.linknum);  //linknum is defined above
                  return "M" + d.source.x + "," + d.source.y + "A" + dr + "," + dr + " 0 0,1 " + d.target.x + "," + d.target.y;
              }
          });
      }

      var drag_handler = d3.drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended);

      drag_handler(nodeObjs);

      var simulation = d3.forceSimulation()
          //.force("charge", d3.forceManyBody().strength(-300/Math.sqrt(num_nodes)))
          .force("charge", d3.forceManyBody().strength(-500))
          .force("center", d3.forceCenter(x_center, y_center))
          .force("link", d3.forceLink().id(function(d) { return d.id; }));

      simulation
          .nodes(graph_nodes)
          .on("tick", ticked);

      simulation.force("link")
          .links(graph_links);

  })
  .catch(function(error) { console.log(error); });
}
