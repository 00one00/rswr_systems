document.addEventListener('DOMContentLoaded', function() {
    console.log('Status Chart: Starting initialization');
    
    // Check if D3 is available
    if (typeof d3 === 'undefined') {
        console.error('Status Chart: D3.js not loaded');
        return;
    }
    
    // Check if container exists
    const container = document.getElementById('status-container');
    if (!container) {
        console.error('Status Chart: Container not found');
        return;
    }
    
    // Check if chart container exists
    const chartContainer = document.getElementById('status-chart');
    if (!chartContainer) {
        console.error('Status Chart: Chart container not found');
        return;
    }
    
    // Constants and configuration
    const containerWidth = container.clientWidth || 600;
    const width = Math.min(600, containerWidth * 0.9);
    const height = 380;
    const margin = {top: 20, right: 170, bottom: 20, left: 20}; // Increased right margin for legend
    const radius = Math.min((width - margin.left - margin.right) / 2, (height - margin.top - margin.bottom) / 2); // Adjusted radius
    
    console.log('Status Chart: Container width:', containerWidth, 'Chart width:', width);
    
    // DOM setup
    const svg = d3.select('#status-chart')
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('preserveAspectRatio', 'xMidYMid meet');
    
    // Create a group for the pie chart, centered within the available space
    const pieGroup = svg.append('g')
        .attr('transform', `translate(${(width - margin.right) / 2}, ${height / 2})`);
    
    // Create a separate group for the legend
    const legendGroup = svg.append('g')
        .attr('class', 'legend-group')
        .attr('transform', `translate(${width - margin.right + 20}, ${height / 2 - 100})`);
        
    // Color scale for status types
    const colorScale = d3.scaleOrdinal()
        .domain(['REQUESTED', 'PENDING', 'APPROVED', 'IN_PROGRESS', 'COMPLETED', 'DENIED'])
        .range(['#6c757d', '#ffc107', '#17a2b8', '#007bff', '#28a745', '#dc3545']);
    
    // Get repair status data from the page context
    // Format: [{status: "STATUS", count: X}, ...]
    
    const repairStatusData = [
        {status: 'REQUESTED', count: parseInt(document.getElementById('stats-requested')?.textContent || '0')},
        {status: 'PENDING', count: parseInt(document.getElementById('stats-pending')?.textContent || '0')},
        {status: 'APPROVED', count: parseInt(document.getElementById('stats-approved')?.textContent || '0')},
        {status: 'IN_PROGRESS', count: parseInt(document.getElementById('stats-in-progress')?.textContent || '0')},
        {status: 'COMPLETED', count: parseInt(document.getElementById('stats-completed')?.textContent || '0')},
        {status: 'DENIED', count: parseInt(document.getElementById('stats-denied')?.textContent || '0')}
    ];
    
    console.log('Status Chart: Data loaded:', repairStatusData);
    
    // Filter out statuses with 0 count for the pie chart
    const filteredData = repairStatusData.filter(d => d.count > 0);
    
    // If no data, show a message
    if (filteredData.length === 0) {
        console.log('Status Chart: No filtered data, showing fallback message');
        pieGroup.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '0.35em')
            .style('font-size', '14px')
            .style('fill', '#666')
            .text('No repair data available');
        
        // Also add a simple test circle to verify SVG is working
        pieGroup.append('circle')
            .attr('r', 20)
            .attr('fill', '#ccc')
            .attr('stroke', '#999')
            .attr('stroke-width', 2);
            
        return;
    }
    
    // Create pie generator
    const pie = d3.pie()
        .value(d => d.count)
        .sort(null);
    
    // Create arc generator
    const arc = d3.arc()
        .innerRadius(0)
        .outerRadius(radius - 10); // Slightly smaller to fit within container
    
    // Create outer arc for labels
    const outerArc = d3.arc()
        .innerRadius(radius * 0.85)
        .outerRadius(radius * 0.85);
    
    // Generate pie slices
    const slices = pieGroup.selectAll('.arc')
        .data(pie(filteredData))
        .enter()
        .append('g')
        .attr('class', 'arc');
    
    // Add path for each slice with improved animation
    slices.append('path')
        .attr('d', arc)
        .attr('fill', d => colorScale(d.data.status))
        .attr('stroke', 'white')
        .style('stroke-width', '2px')
        .style('opacity', 0.85)
        .transition()
        .duration(800)
        .attrTween('d', function(d) {
            const interpolate = d3.interpolate({startAngle: 0, endAngle: 0}, d);
            return function(t) {
                return arc(interpolate(t));
            };
        });
    
    // Add percentage labels inside larger slices
    slices.filter(d => (d.endAngle - d.startAngle) > 0.35)
        .append('text')
        .attr('transform', d => `translate(${arc.centroid(d)})`)
        .attr('dy', '.35em')
        .attr('text-anchor', 'middle')
        .style('font-size', '12px')
        .style('font-weight', 'bold')
        .style('fill', 'white')
        .style('pointer-events', 'none')
        .text(d => Math.round((d.endAngle - d.startAngle) / (2 * Math.PI) * 100) + '%');
    
    // Add legend with improved spacing and styling
    const legend = legendGroup.selectAll('.legend')
        .data(filteredData)
        .enter()
        .append('g')
        .attr('class', 'legend')
        .attr('transform', (d, i) => `translate(0, ${i * 30})`); // Increased vertical spacing
    
    // Add colored squares in legend
    legend.append('rect')
        .attr('width', 16)
        .attr('height', 16)
        .attr('rx', 2) // Rounded corners
        .attr('fill', d => colorScale(d.status));
    
    // Add status text
    legend.append('text')
        .attr('x', 24)
        .attr('y', 8)
        .attr('dy', '.35em')
        .style('text-anchor', 'start')
        .style('font-size', '12px')
        .style('fill', '#333')
        .text(d => {
            // Format status text to be more readable (Title Case)
            const formatted = d.status.toLowerCase().replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            return `${formatted} (${d.count})`;
        });
    
    // Add interaction to the legend
    legend.style('cursor', 'pointer')
        .on('mouseover', function(event, d) {
            // Highlight corresponding slice
            slices.selectAll('path')
                .filter(path => path.data.status === d.status)
                .transition()
                .duration(200)
                .style('opacity', 1)
                .attr('transform', 'scale(1.03)');
        })
        .on('mouseout', function() {
            // Restore all slices
            slices.selectAll('path')
                .transition()
                .duration(200)
                .style('opacity', 0.85)
                .attr('transform', 'scale(1)');
        });
        
    // Add total count in the center
    const totalCount = filteredData.reduce((sum, d) => sum + d.count, 0);
    
    pieGroup.append('text')
        .attr('class', 'total-count')
        .attr('text-anchor', 'middle')
        .attr('dy', '-0.5em')
        .style('font-size', '14px')
        .style('fill', '#555')
        .text('Total Repairs');
        
    pieGroup.append('text')
        .attr('class', 'total-count-value')
        .attr('text-anchor', 'middle')
        .attr('dy', '1em')
        .style('font-size', '24px')
        .style('font-weight', 'bold')
        .style('fill', '#333')
        .text(totalCount);
    
    console.log('Status Chart: Chart creation completed successfully');
}); 