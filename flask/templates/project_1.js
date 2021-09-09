var data1 = [0.65958,0.65958,0.65958,0.65958,0.65958,0.65958,0.65958,0.65958,0.65958];
var data2 = [0.51326,0.51326,0.51326,0.51326,0.51326,0.51326,0.51326,0.51326,0.51326];
var data3 = [0.66234,0.67282,0.65544,0.66946,0.66636,0.66582,0.66545,0.65449,0.66738];
var data4 = [0.50101,0.50437,0.50382,0.50279,0.50412,0.50371,0.50403,0.48827,0.50216];
var data5 = [0.74569,0.75426,0.73686,0.75788,0.76652,0.77094,0.74951,0.74736,0.76999];
var data6 = [0.68776,0.6936,0.67802,0.69944,0.6949,0.69495,0.69136,0.67325,0.69913];
var data7 = [0.78743,0.80853,0.78567,0.80722,0.81883,0.82671,0.79118,0.78171,0.82629];
var data8 = [0.79244,0.79849,0.7776,0.80524,0.79743,0.79809,0.78843,0.73149,0.80614];
var data9 = [0.78752,0.81229,0.81117,0.82155,0.83349,0.84265,0.81756,0.79909,0.81751];

var svg = d3.select('svg'),
    margin = {top: 20, right: 0, bottom: 30, left: 40},
    svgWidth = +svg.attr('width') - margin.left - margin.right,
    svgHeight = +svg.attr("height") - margin.top - margin.bottom,
    g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")")
    plotHeight = svgHeight+20,
    plotWidth = svgWidth*.9;

// svg.append('rect')
//     .attr('width','100%')
//     .attr('height','100%')
//     .attr('fill','black')
    
var barPadding = 0;
var barGroupWidth = plotWidth / 9;
var barWidth = barGroupWidth/10;
var groupPadding = barWidth;

var dataAll = d3.merge([data1,data2,data3,data4,data5,data6,data7,data8,data9]);

var colors = d3.scaleLinear()
    .domain([1, 9])
    .range([d3.rgb(51,48,133),d3.rgb(215,185,85)]);

var colors2 = [d3.rgb(51,48,133),d3.rgb(57,101,175),
    d3.rgb(41,129,196), d3.rgb(0,165,197),
    d3.rgb(56,182,155), d3.rgb(144,190,114),
    d3.rgb(215,185,85), d3.rgb(251,205,47),d3.rgb(241,233,35)];

var min_funcs =['Torque','Torque2','Force','Force2',
    'Active State','Active State2','Neural Drive',
    'Neural Drive2','Energy'];

// Bar Chart
var barChart = svg.selectAll('barChart')
    .data(dataAll)
    .enter()
    .append("rect")
    .attr('x',function(d,i) {
        return 70+barWidth*(i%9) + (barGroupWidth+groupPadding/2)*Math.floor(i/9);
    })
    .attr('y',function(d) { 
        return  2*(plotHeight-d*plotHeight)-45; 
    })
    .attr("height",function(d) { 
        return  2*(d-.45)*plotHeight; 
    })
    .attr("width",  barWidth - barPadding)
    .style('stroke', 'black')
    .style('stroke-width',.5)
    .style('fill', function(d,i) {
        return colors2[i%9];
    })
    .on('mouseover',function(d,i){

        if( d3.select(this).attr('opacity')==1){
            barChart.attr('baron',1)
        } else {
            barChart.attr('baron',0)
        }
        
        if (tooltip1.attr('active')==1){
            d3.select(this).attr('opacity',1)
        } else {
            if (bartooltip2.attr('barselect')==-1){
                barChart.attr('opacity',.5)
            }
            d3.select(this).attr('opacity',1)
        }

        if (bartooltip2.attr('barselect')==i){
            d3.select(this).attr('opacity',1)
        }

    })
    .on("mousemove", function(d,i){
        bartooltip
        .text(d)
        .style('visibility','visible')
        .style("top", 2*(plotHeight-d*plotHeight)-75 +"px")
        .style("left",55+barWidth*(i%9) + (barGroupWidth+groupPadding/2)*Math.floor(i/9)+"px");    
    })
    .on('mouseout',function(d,i){
        if (bartooltip2.attr('barselect')==i){
            d3.select(this).attr('opacity',1)
        } else if (bartooltip2.attr('barselect')>=0){
            if (barChart.attr('baron')==0){
                d3.select(this).attr('opacity',.5)
            }
        } else if (bartooltip2.attr('barselect')==-1 && tooltip1.attr('active')==0){
            barChart.attr('opacity',1)
        } else if (bartooltip2.attr('barselect')==-1 && tooltip1.attr('active')==1){
            if (barChart.attr('baron')==0){
                d3.select(this).attr('opacity',.5)
            } else {
                d3.select(this).attr('opacity',1)
            }
        }
        bartooltip.style('visibility','hidden')
    })
    .on('click',function(d,i){

        if (bartooltip2.attr('active') == 0){
            bartooltip2.attr('active',1)
                .text(d)
                .attr('barselect',i)
                .style('visibility','visible')
                .style("top", 2*(plotHeight-d*plotHeight)-75+"px")
                .style("left",55+barWidth*(i%9) + (barGroupWidth+groupPadding/2)*Math.floor(i/9)+"px");
        }
        else if (bartooltip2.attr('active') == 1 && bartooltip2.attr('barselect')==i){
            d3.select(this).attr('opacity',.5)
            barChart.attr('baron',0)
            bartooltip.style('visibility','hidden')
            bartooltip2.attr('active',0) 
                .text(d)
                .attr('barselect',-1)
                .style('visibility','hidden')
                .style("top", 2*(plotHeight-d*plotHeight)-75+"px")
                .style("left",55+barWidth*(i%9) + (barGroupWidth+groupPadding/2)*Math.floor(i/9)+"px");
        }   
        else if (bartooltip2.attr('active') == 1){
            barChart.attr('opacity',function(d,i){
                if (i == bartooltip2.attr('barselect')){
                    return .5
                } else {
                    return d3.select(this).attr('opacity')
                }
            })
            bartooltip2.attr('active',1) 
                .attr('barselect',i)
                .text(d)
                .style('visibility','visible')
                .style("top", 2*(plotHeight-d*plotHeight)-75+"px")
                .style("left",55+barWidth*(i%9) + (barGroupWidth+groupPadding/2)*Math.floor(i/9)+"px");
        }
    })
    ;
var bartooltip = d3.select("body")
    .append("div")
    .attr('active',0)
    .style("position", "absolute")
    .style("z-index", "10")
    .style("visibility", "hidden")
    .style('color','white')
    .text("a simple tooltip");

var bartooltip2 = d3.select("body")
    .append("div")
    .attr('barselect',-1)
    .attr('active',0)
    .style("position", "absolute")
    .style("z-index", "10")
    .style("visibility", "hidden")
    .style('color','white')
    .text("a simple tooltip");

// Axis
// Create scale
var xdomain = d3.extent(min_funcs,function(d){
        return d;
    });

var scalex = d3.scaleLinear()
    .domain([1,9])
    .range([30, plotWidth]);

var scaley = d3.scaleLinear()
    .domain([.85,.45])
    .range([0, 2*(.85-.45)*plotHeight]);

// Add scales to axis
var x_axis = d3.axisBottom()
    .scale(scalex)
    .ticks(9)
    .tickSize(0)
    .tickFormat(function(d,i){
        return min_funcs[i];
    });

var y_axis = d3.axisLeft()
    .scale(scaley)
    .ticks(9);

//Append group and insert axis
var xaxisshiftx = barGroupWidth+barWidth+barPadding+25;
var xaxisshifty = plotHeight-10;
var xaxisshiftx2 = barGroupWidth+barWidth+barPadding+0;

svg.append("g")
    .attr('transform','translate('+xaxisshiftx2+','+xaxisshifty+')')
    .attr('class','axisRed')
    .call(x_axis);

svg.append('g')
    .call(y_axis)
    .attr('class','axisWhite')
    .attr('transform','translate('+54+','+50.5+')');

svg.append('line')
    .style('stroke','white')
    .style('stroke-width',1)
    .attr('x1',xaxisshiftx-barGroupWidth/2+3)
    .attr('y1',xaxisshifty-3)
    .attr('x2',xaxisshiftx-22+plotWidth+barGroupWidth/2)
    .attr('y2',xaxisshifty-3);

// Labels
svg.append('text')
    .attr('x',plotWidth/2+barGroupWidth)
    .attr('y',20)
    .style('text-anchor','middle')
    .style('fill','white')
    .text("Computed R Squared Values for Proxy Fits by Minimization Function")

svg.append('text')
    .attr('x',plotWidth/2+barGroupWidth)
    .attr('y',plotHeight+20)
    .style('text-anchor','middle')
    .style('fill','white')
    .text("Neuromechanical Proxy")

svg.append('text')
    .attr('transform','rotate(-90)')
    .attr('y',20)
    .attr('x',0-plotHeight/2)
    .style('text-anchor','middle')
    .style('fill','white')
    .text('R Squared Value');

// Legend
var legendRectSize = barWidth;
var legendSpacing = 5;

var legend = svg.selectAll('.legend')
  .data(colors2)
  .enter()
  .append('g')
  .attr('class', 'legend')
  .style('fill','white')
  .attr('transform', function(d, i) {
    var height = legendRectSize + legendSpacing;
    var offset =  height * colors2.length / 2;
    var horz = 2 * legendRectSize;
    var vert = legendRectSize*9 + i * height - offset;
    return 'translate(' + horz + ',' + vert + ')';
  })
  ;
legend.append('text')
  .attr('x', legendRectSize + legendSpacing+50)
  .attr('y', legendRectSize - legendSpacing+45)
  .text(function(d,i) { return min_funcs[i] ; })
  .attr('font-size',12)
  .style('fill','white');

legend.append('circle')
    .attr('r', legendRectSize/2)
    .style('fill', function(d,i){
        return colors2[i]
    })
    .style('stroke', function(d,i){
        return colors2[i]
    })
    .attr('transform','translate('+53+','+41+')')
    .on('click',function(d,i){
        tooltip1.attr('selectedmin',i);
        var k;
        var text = "";
        var fitnum = i;
        var d1  = [data1[fitnum],data2[fitnum],
            data3[fitnum],data4[fitnum],data5[fitnum],
            data6[fitnum],data7[fitnum],data8[fitnum],
            data9[fitnum]];
        for (k = 1; k < 10; k++) {
            if (eval('tooltip'+k+'.attr('+'"active"'+')')==0){
                eval('tooltip'+k+'.attr('+'"active"'+',1)')
                eval('tooltip'+k+'.attr('+'"min_func_num",'+i+')')
            }
            else if (eval('tooltip'+k+'.attr('+'"active"'+')')==1 && eval('tooltip'+k+'.attr('+'"min_func_num"'+')')==i){
                eval('tooltip'+k+'.attr('+'"active"'+',0)')
                eval('tooltip'+k+'.style('+'"visibility"'+','+'"hidden"'+')')
                tooltip1.attr('selectedmin',-1)
                legend.attr('opacity',1)
                if (bartooltip2.attr('barselect')==-1){
                    barChart.attr('opacity',1)
                } else {
                    barChart.attr('opacity',function(d,i){
                        if (fitnum == i%9) {
                            return .5
                        } else {
                            if (bartooltip2.attr('barselect')==i)
                                return 1
                            else {
                                return .5
                            }
                        }
                    });
                }
            }
            else if (eval('tooltip'+k+'.attr('+'"active"'+')')==1 && eval('tooltip'+k+'.attr('+'"min_func_num"'+')')!=i){
                eval('tooltip'+k+'.attr('+'"active"'+',1)')
                eval('tooltip'+k+'.attr('+'"min_func_num",'+i+')')
                var ind = k-1
                var r_sq = d1[ind]
                eval('tooltip'+k+'.text(d1['+ind+']).style("visibility","visible").style("top",2*(plotHeight-r_sq*plotHeight)-80 +"px").style')
                eval('tooltip'+k+'.style("left",45+barWidth*(i%9) + (barGroupWidth+groupPadding/2)*'+ind+'+"px")')
                barChart.attr('opacity',function(d,i){
                    if (fitnum == i%9) {
                        return 1
                    } else {
                        if (bartooltip2.attr('barselect')==i)
                            return 1
                        else {
                            return .5
                        }
                    }
                });
                legend.attr('opacity',function(d,i){
                    if (fitnum == i) {return 1}
                        else {return .5}
                });
            }
        }
    })
    .on('mouseover',function(d,i){
        var fitnum = i;
        var d1  = [data1[fitnum],data2[fitnum],
            data3[fitnum],data4[fitnum],data5[fitnum],
            data6[fitnum],data7[fitnum],data8[fitnum],
            data9[fitnum]];
        var k;
        if (tooltip1.attr('selectedmin')==-1 || tooltip1.attr('selectedmin')==i){
            if (tooltip1.style('visibility')!='visible'){
                for (k = 1; k < 10; k++) {
                    ind = k-1;
                    var r_sq = d1[ind];
                    eval('tooltip'+k+
                        '.text(d1['+ind+'])'+
                        '.style("visibility","visible")'+
                        '.style("top", 2*(plotHeight-'+r_sq+'*plotHeight)-75 +"px")'+
                        '.style("left",55+barWidth*('+i+'%9) + (barGroupWidth+groupPadding/2)*'+ind+'+"px");')
                }
            }
        
            barChart.attr('opacity',function(d,i){
                    if (fitnum == i%9) {
                        return 1
                    } else {
                        if (bartooltip2.attr('barselect')==i)
                            return 1
                        else {
                            return .5
                        }
                    }
            });
            legend.attr('opacity',function(d,i){
                if (fitnum == i) {return 1}
                    else {return .5}
            });
        }
    })
    .on('mouseout',function(){
        if (tooltip1.attr('active')==0)
            tooltip1.style("visibility", "hidden");
        if (tooltip2.attr('active')==0)
            tooltip2.style("visibility", "hidden");
        if (tooltip3.attr('active')==0)
            tooltip3.style("visibility", "hidden");
        if (tooltip4.attr('active')==0)
            tooltip4.style("visibility", "hidden");
        if (tooltip5.attr('active')==0)
            tooltip5.style("visibility", "hidden");
        if (tooltip6.attr('active')==0)
            tooltip6.style("visibility", "hidden");
        if (tooltip7.attr('active')==0)
            tooltip7.style("visibility", "hidden");
        if (tooltip8.attr('active')==0)
            tooltip8.style("visibility", "hidden");
        if (tooltip9.attr('active')==0)
            tooltip9.style("visibility", "hidden");

        if (bartooltip2.attr('barselect')==-1 && tooltip1.attr('selectedmin')==-1){
            barChart.attr('opacity',1)
        } else {
            barChart.attr('opacity',function(d,i){
                    if (fitnum == i%9) {
                        return .5
                    } else {
                        if (bartooltip2.attr('barselect')==i)
                            return 1
                        else {
                            return .5
                        }
                    }
            });
        }
        legend.attr('opacity',1)
        // d3.select(this)
        //     .attr('opacity',1);
    })
    ;

var tooltip1 = d3.select("body")
    .append("div")
    .style("position", "absolute")
    .style("z-index", "10")
    .style("visibility", "hidden")
    .style('color','white')
    .attr('active',0)
    .attr('min_func_num',0)
    .attr('selectedmin',-1)
    .text("a simple tooltip");

var tooltip2 = d3.select("body")
    .append("div")
    .style("position", "absolute")
    .style("z-index", "10")
    .style("visibility", "hidden")
    .style('color','white')
    .attr('active',0)
    .attr('min_func_num',0)
    .text("a simple tooltip");

var tooltip3 = d3.select("body")
    .append("div")
    .style("position", "absolute")
    .style("z-index", "10")
    .style("visibility", "hidden")
    .style('color','white')
    .attr('active',0)
    .attr('min_func_num',0)
    .text("a simple tooltip");

var tooltip4 = d3.select("body")
    .append("div")
    .style("position", "absolute")
    .style("z-index", "10")
    .style("visibility", "hidden")
    .style('color','white')
    .attr('active',0)
    .attr('min_func_num',0)
    .text("a simple tooltip");

var tooltip5 = d3.select("body")
    .append("div")
    .style("position", "absolute")
    .style("z-index", "10")
    .style("visibility", "hidden")
    .style('color','white')
    .attr('active',0)
    .attr('min_func_num',0)
    .text("a simple tooltip");

var tooltip6 = d3.select("body")
    .append("div")
    .style("position", "absolute")
    .style("z-index", "10")
    .style("visibility", "hidden")
    .style('color','white')
    .attr('active',0)
    .attr('min_func_num',0)
    .text("a simple tooltip");

var tooltip7 = d3.select("body")
    .append("div")
    .style("position", "absolute")
    .style("z-index", "10")
    .style("visibility", "hidden")
    .style('color','white')
    .attr('active',0)
    .attr('min_func_num',0)
    .text("a simple tooltip");

var tooltip8 = d3.select("body")
    .append("div")
    .style("position", "absolute")
    .style("z-index", "10")
    .style("visibility", "hidden")
    .style('color','white')
    .attr('active',0)
    .attr('min_func_num',0)
    .text("a simple tooltip");

var tooltip9 = d3.select("body")
    .append("div")
    .style("position", "absolute")
    .style("z-index", "10")
    .style("visibility", "hidden")
    .style('color','white')
    .attr('active',0)
    .attr('min_func_num',0)
    .text("a simple tooltip");



// legend.append('text')
//   .attr('x', legendRectSize + legendSpacing)
//   .attr('y', legendRectSize - legendSpacing)
//   .text(function(d) { return min_funcs(d); });



// var barChart2 = svg.selectAll("rect")
//     .data(data2)
//     .enter()
//     .append("rect")
//     .attr('x',function(d,i) {
//         return barWidth*i + barGroupWidth ;
//     })
//     .attr('y',function(d) { 
//         return  svgHeight-d*svgHeight; 
//     })
//     .attr("height",function(d) { 
//         return  d*svgHeight; 
//     })
//     .attr("width",  barWidth - barPadding)
//     .style('stroke', function(d,i) {
//         return colors;
//     })
//     .style('fill', function(d,i) {
//         return 'purple';
//     });

// var circle = svg.selectAll("circle")
//     .data(dataset)
//     .enter()
//     .append("circle")
//     .attr("cy", function(d) {
//          return svgHeight - d 
//     })
//     .attr("r", function(d){
//         return d/10;
//     })
//     .attr("transform", function (d, i) {
//         var translate = [barWidth * i + barWidth/2, 0]; 
//         return "translate("+ translate +")";
//     })
//     .style('stroke', function(d,i) {
//         return colors;
//     })
//     .style('fill', function(d,i) {
//         return 'purple';
//     })

// circle.style('fill','orange')



// var data2 = [{
//     'name': 'Torque',
//     'value': 0.65958,
// },{
//     'name': 'Torque2',
//     'value': 0.51326,
// },{
//     'name': 'Force',
//     'value': 0.66234,
// },{
//     'name': 'Froce2',
//     'value': 0.50101,
// },{
//     'name': 'Active State',
//     'value': 0.74569,
// },{
//     'name': 'Active State2',
//     'value': 0.68776,
// },{
//     'name': 'Drive',
//     'value': 0.78743,
// },{
//     'name': 'Drive2',
//     'value': 0.79244,
// },{
//     'name': 'Energy',
//     'value': 0.78752}];