// Simple test to verify charts can render
console.log('=== TEST CHART SCRIPT LOADED ===');

document.addEventListener('DOMContentLoaded', function() {
    console.log('Test Chart: DOM ready');
    
    // Test if we can add simple content to chart containers
    const containers = ['status-chart', 'unit-chart', 'cost-chart'];
    
    containers.forEach((id, index) => {
        const container = document.getElementById(id);
        if (container) {
            console.log(`Test Chart: Found container ${id}`);
            
            // Add a simple test element
            const testDiv = document.createElement('div');
            testDiv.style.cssText = `
                background: #f0f8ff;
                border: 2px solid #4a90e2;
                padding: 20px;
                text-align: center;
                font-family: Arial, sans-serif;
                color: #333;
                border-radius: 8px;
                margin: 10px;
            `;
            testDiv.innerHTML = `
                <h4>Test Chart ${index + 1}</h4>
                <p>Container: ${id}</p>
                <p>This is a test to verify the container works</p>
                <div style="background: #e3f2fd; padding: 10px; margin-top: 10px; border-radius: 4px;">
                    Container Width: ${container.clientWidth}px<br>
                    Container Height: ${container.clientHeight}px
                </div>
            `;
            
            container.appendChild(testDiv);
            console.log(`Test Chart: Added test content to ${id}`);
        } else {
            console.error(`Test Chart: Container ${id} not found`);
        }
    });
    
    // Test D3 availability
    if (typeof d3 !== 'undefined') {
        console.log('Test Chart: D3.js is available, version:', d3.version);
        
        // Try to create a simple D3 element in the status chart
        const statusChart = document.getElementById('status-chart');
        if (statusChart) {
            const svg = d3.select('#status-chart')
                .append('svg')
                .attr('width', 200)
                .attr('height', 100)
                .style('border', '1px solid #ccc')
                .style('margin', '10px');
                
            svg.append('circle')
                .attr('cx', 100)
                .attr('cy', 50)
                .attr('r', 30)
                .attr('fill', '#4a90e2')
                .attr('stroke', '#333')
                .attr('stroke-width', 2);
                
            svg.append('text')
                .attr('x', 100)
                .attr('y', 55)
                .attr('text-anchor', 'middle')
                .style('font-family', 'Arial')
                .style('font-size', '14px')
                .style('fill', 'white')
                .text('D3 Works!');
                
            console.log('Test Chart: Created D3 test element');
        }
    } else {
        console.error('Test Chart: D3.js not available');
    }
});