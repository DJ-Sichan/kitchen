$(document).ready(function() {
    setupClickHandlers();
});

function setupClickHandlers() {
    /**
     * Assign click handlers to all sidebar entries.
     */
    $('.sidebar_link').click(function() {
        var parameters = {};
        var active_buttons = $('.active .sidebar_link');
        if (active_buttons.index(this) > -1) {
            active_buttons = active_buttons.not(this);
        } else {
            // active_buttons.add(this);
            active_buttons = $.fn.add.call(active_buttons, this);
        }
        var changed_environment = false;
        var changed_virt = false;
        // Add already selected buttons to the params
        for (var i=0; i < active_buttons.length; i++) {
            var datatype = active_buttons[i].dataset['type'];
            var dataname = active_buttons[i].dataset['name'];
            if (datatype === 'env') {
                if (active_buttons[i] === this) {
                    parameters[datatype] = dataname;
                    changed_environment = true;
                } else if (!changed_environment) {
                    parameters[datatype] = dataname;
                }
            } else if (datatype === 'virt') {
                if (active_buttons[i] === this) {
                    parameters[datatype] = dataname;
                    changed_virt = true;
                } else if (!changed_virt) {
                    parameters[datatype] = dataname;
                }
            } else {
                if (datatype in parameters && datatype !== 'env') {
                    parameters[datatype] += ',' + dataname;
                } else {
                    parameters[datatype] = dataname;
                }
            }
        }

        // If there are no env or virt selections set parameter to an empty string
        // to prevent server-side defaults from setting them
        var datatypes = ['env', 'roles', 'options'];
        if ( show_virt ) { datatypes.push('virt'); }
        for (var datatype in datatypes) {
            if (!(datatypes[datatype] in parameters)) {
                parameters[datatypes[datatype]] = "";
            }
        }

        // Build url parameters
        var pathName = window.location.pathname;
        if (pathName == '/'){
            var url = 'api/nodes/?extended=true?';
            // Remove trailing '&'
            for (var param in parameters) {
                url += param + '=' + parameters[param] + '&';
            }
            // Draw new table
            $.getJSON(url.slice(0, -1), function(data){
                drawNodesTable(data);
            });
        } else {
            var url = '?';
            // Remove trailing '&'
            for (var param in parameters) {
                url += param + '=' + parameters[param] + '&';
            }
            // Redirect to new url
            window.location = url.slice(0, -1);
        }
    });
}
