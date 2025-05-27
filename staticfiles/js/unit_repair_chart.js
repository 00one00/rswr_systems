document.addEventListener('DOMContentLoaded', function() {
    console.log('Unit Repair Chart: DOMContentLoaded event triggered');
    
    // Constants and configuration
    const containerWidth = document.getElementById('unit-container').clientWidth;
    const width = Math.min(800, containerWidth * 0.95);
    const height = 380;
    const margin = {top: 30, right: 30, bottom: 80, left: 60};
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    // DOM setup
    const svg = d3.select('#unit-chart')
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('preserveAspectRatio', 'xMidYMid meet')
        .append('g')
        .attr('transform', `translate(${margin.left}, ${margin.top})`);
    
    // Add title
    svg.append('text')
        .attr('class', 'chart-title')
        .attr('x', innerWidth / 2)
        .attr('y', -margin.top / 2)
        .attr('text-anchor', 'middle')
        .style('font-size', '14px')
        .style('font-weight', 'bold')
        .style('fill', '#555')
        .text('Top Units by Repair Count');
    
    // Create loading indicator
    const loadingIndicator = d3.select('#unit-chart')
        .append('div')
        .attr('class', 'loading-indicator')
        .style('position', 'absolute')
        .style('top', '50%')
        .style('left', '50%')
        .style('transform', 'translate(-50%, -50%)')
        .text('Loading data...');
    
    // Create error message container (hidden initially)
    const errorContainer = d3.select('#unit-chart')
        .append('div')
        .attr('class', 'error-message')
        .style('position', 'absolute')
        .style('top', '50%')
        .style('left', '50%')
        .style('transform', 'translate(-50%, -50%)')
        .style('display', 'none')
        .style('color', '#d9534f')
        .style('text-align', 'center')
        .text('Error loading data');
    
    // Generate sample data
    function generateSampleData() {
        return [
            {unit_number: 'Unit 1', repair_count: 5},
            {unit_number: 'Unit 2', repair_count: 3},
            {unit_number: 'Unit 3', repair_count: 7},
            {unit_number: 'Unit 4', repair_count: 2},
            {unit_number: 'Unit 5', repair_count: 4},
            {unit_number: 'Unit 6', repair_count: 6},
            {unit_number: 'Unit 7', repair_count: 1}
        ];
    }
    
    // Function to create the chart
    function createChart(data) {
        console.log('Creating unit repair chart with data:', data);
        
        // Hide error message if it was showing
        errorContainer.style('display', 'none');
        
        // If no data or empty array, show placeholder message
        if (!data || data.length === 0) {
            svg.append('text')
                .attr('class', 'no-data-message')
                .attr('x', innerWidth / 2)
                .attr('y', innerHeight / 2)
                .attr('text-anchor', 'middle')
                .style('font-size', '14px')
                .style('fill', '#777')
                .text('No repair data available');
            
            return;
        }
        
        // Clear any previous chart elements
        svg.selectAll('.bar, .axis, .grid, .axis-label, .bar-label, .no-data-message').remove();
        
        // Normalize data to ensure consistent property names
        const normalizedData = data.map(item => ({
            unit_number: item.unit_number || item.unitNumber || 'Unknown',
            repair_count: parseInt(item.count || item.repair_count || 0)
        }));
        
        // Sort data by repair count in descending order
        normalizedData.sort((a, b) => b.repair_count - a.repair_count);
        
        // Limit to top 8 units for better display
        const displayData = normalizedData.length > 8 ? normalizedData.slice(0, 8) : normalizedData;
        
        // Create scales
        const x = d3.scaleBand()
            .domain(displayData.map(d => d.unit_number))
            .range([0, innerWidth])
            .padding(0.25);
        
        const y = d3.scaleLinear()
            .domain([0, d3.max(displayData, d => d.repair_count) * 1.2 || 5])  // Fallback to 5 if no data
            .nice()
            .range([innerHeight, 0]);
        
        // Create and add x-axis
        svg.append('g')
            .attr('class', 'axis x-axis')
            .attr('transform', `translate(0, ${innerHeight})`)
            .call(d3.axisBottom(x))
            .selectAll('text')
            .attr('transform', 'translate(-10,0)rotate(-45)')
            .style('text-anchor', 'end')
            .style('font-size', '12px')
            .style('font-weight', '500');
        
        // Add x-axis label
        svg.append('text')
            .attr('class', 'axis-label')
            .attr('x', innerWidth / 2)
            .attr('y', innerHeight + margin.bottom - 10)
            .attr('text-anchor', 'middle')
            .style('font-size', '12px')
            .style('fill', '#555')
            .text('Unit Number');
        
        // Create and add y-axis
        svg.append('g')
            .attr('class', 'axis y-axis')
            .call(d3.axisLeft(y)
                .ticks(5)
                .tickFormat(d => Math.floor(d) === d ? d : ''));
        
        // Add y-axis label
        svg.append('text')
            .attr('class', 'axis-label')
            .attr('transform', 'rotate(-90)')
            .attr('y', -margin.left + 15)
            .attr('x', -innerHeight / 2)
            .attr('dy', '1em')
            .style('text-anchor', 'middle')
            .style('font-size', '12px')
            .style('fill', '#555')
            .text('Number of Repairs');
        
        // Add horizontal grid lines
        svg.append('g')
            .attr('class', 'grid')
            .call(d3.axisLeft(y)
                .ticks(5)
                .tickSize(-innerWidth)
                .tickFormat(''))
            .selectAll('line')
            .style('stroke', '#e0e0e0')
            .style('stroke-dasharray', '3,3');
        
        // Create gradient
        const gradient = svg.append('defs')
            .append('linearGradient')
            .attr('id', 'bar-gradient')
            .attr('gradientUnits', 'userSpaceOnUse')
            .attr('x1', 0)
            .attr('y1', y(0))
            .attr('x2', 0)
            .attr('y2', y(d3.max(displayData, d => d.repair_count) || 5)); // Fallback to 5 if no data
            
        gradient.append('stop')
            .attr('offset', '0%')
            .attr('stop-color', '#4d94ff');
            
        gradient.append('stop')
            .attr('offset', '100%')
            .attr('stop-color', '#0056b3');
        
        // Create and add bars
        svg.selectAll('.bar')
            .data(displayData)
            .enter()
            .append('rect')
            .attr('class', 'bar')
            .attr('x', d => x(d.unit_number))
            .attr('width', x.bandwidth())
            .attr('y', d => y(d.repair_count))
            .attr('height', d => innerHeight - y(d.repair_count))
            .attr('rx', 3)
            .attr('fill', 'url(#bar-gradient)')
            .attr('stroke', '#0056b3')
            .attr('stroke-width', 0.5)
            .attr('stroke-opacity', 0.5);
        
        // Add text labels on top of the bars
        svg.selectAll('.bar-label')
            .data(displayData)
            .enter()
            .append('text')
            .attr('class', 'bar-label')
            .attr('x', d => x(d.unit_number) + x.bandwidth() / 2)
            .attr('y', d => y(d.repair_count) - 8)
            .attr('text-anchor', 'middle')
            .style('font-size', '12px')
            .style('font-weight', 'bold')
            .text(d => d.repair_count);
    }
    
    // Fetch data from API with retry mechanism
    function fetchDataWithRetry(url, retries = 2) {
        console.log(`Unit Repair Chart: Fetching data from ${url}, retries left: ${retries}`);
        
        return fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Network response was not ok: ${response.status}`);
                }
                return response.text();
            })
            .then(text => {
                // Log raw response
                console.log('Unit Repair Chart: Raw API response:', text);
                
                if (!text || text.trim() === '') {
                    console.log('Unit Repair Chart: Empty response, returning empty array');
                    return [];
                }
                
                try {
                    return JSON.parse(text);
                } catch (e) {
                    console.error('Unit Repair Chart: Error parsing JSON:', e);
                    throw new Error('Invalid JSON response');
                }
            })
            .catch(error => {
                console.error('Unit Repair Chart: Error fetching data:', error);
                
                if (retries > 0) {
                    console.log(`Unit Repair Chart: Retrying (${retries} left)...`);
                    return new Promise(resolve => {
                        setTimeout(() => {
                            resolve(fetchDataWithRetry(url, retries - 1));
                        }, 1000); // 1 second delay before retry
                    });
                }
                
                throw error;
            });
    }
    
    // Main function to load data and create chart
    function loadDataAndCreateChart() {
        console.log('Unit Repair Chart: Fetching data from API...');
        
        fetchDataWithRetry('/customer/api/unit-repair-data/')
            .then(data => {
                // Remove loading indicator
                loadingIndicator.remove();
                
                console.log('Unit Repair Chart: Processed data:', data);
                
                // Create chart with the data, or sample data as a last resort
                if (Array.isArray(data) && data.length > 0) {
                    createChart(data);
                } else if (typeof data === 'object' && !Array.isArray(data)) {
                    // Convert object to array if needed
                    const dataArray = Object.entries(data).map(([key, value]) => ({
                        unit_number: key,
                        repair_count: typeof value === 'number' ? value : parseInt(value) || 0
                    }));
                    
                    createChart(dataArray);
                } else {
                    console.log('Unit Repair Chart: No valid data, using sample data');
                    createChart(generateSampleData());
                }
            })
            .catch(error => {
                // Remove loading indicator
                loadingIndicator.remove();
                
                // Show error message
                errorContainer.style('display', 'block');
                errorContainer.text(`Error loading data: ${error.message}`);
                
                console.error('Unit Repair Chart: Fatal error:', error);
                
                // Fall back to sample data
                createChart(generateSampleData());
            });
    }
    
    // Start loading data
    loadDataAndCreateChart();
}); 