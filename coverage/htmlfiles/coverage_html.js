// Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
// For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

// Coverage.py HTML report browser code.
/*jslint browser: true, sloppy: true, vars: true, plusplus: true, maxerr: 50, indent: 4 */
/*global coverage: true, document, window, $ */

coverage = {};

function debounce(callback, wait) {
    let timeoutId = null;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            callback.apply(this, args);
        }, wait);
    };
};

function clamp(n, min, max) {
    return Math.min(Math.max(min, n), max);
}

// Find all the elements with data-shortcut attribute, and use them to assign a shortcut key.
coverage.assign_shortkeys = function () {
    document.querySelectorAll("[data-shortcut]").forEach(element => {
        document.addEventListener("keypress", event => {
            if (event.target.tagName.toLowerCase() === "input") {
                return; // ignore keypress from search filter
            }
            if (event.key === element.dataset.shortcut) {
                element.click();
            }
        });
    });
};

// Create the events for the filter box.
coverage.wire_up_filter = function () {
    // Cache elements.
    const table = document.querySelector("table.index");
    const table_body_rows = table.querySelectorAll("tbody tr");
    const no_rows = document.getElementById("no_rows");

    // Observe filter keyevents.
    document.getElementById("filter").addEventListener("input", debounce(event => {
        // Keep running total of each metric, first index contains number of shown rows
        const totals = new Array(table.rows[0].cells.length).fill(0);
        // Accumulate the percentage as fraction
        totals[totals.length - 1] = { "numer": 0, "denom": 0 };

        // Hide / show elements.
        table_body_rows.forEach(row => {
            if (!row.cells[0].textContent.includes(event.target.value)) {
                // hide
                row.classList.add("hidden");
                return;
            }

            // show
            row.classList.remove("hidden");
            totals[0]++;

            for (let column = 1; column < totals.length; column++) {
                // Accumulate dynamic totals
                cell = row.cells[column]
                if (column === totals.length - 1) {
                    // Last column contains percentage
                    const [numer, denom] = cell.dataset.ratio.split(" ");
                    totals[column]["numer"] += parseInt(numer, 10);
                    totals[column]["denom"] += parseInt(denom, 10);
                } else {
                    totals[column] += parseInt(cell.textContent, 10);
                }
            }
        });

        console.log(totals)

        // Show placeholder if no rows will be displayed.
        if (!totals[0]) {
            // Show placeholder, hide table.
            no_rows.style.display = "block";
            table.style.display = "none";
            return;
        }

        // Hide placeholder, show table.
        no_rows.style.display = null;
        table.style.display = null;

        // Calculate new dynamic sum values based on visible rows.
        for (let column = 1; column < totals.length; column++) {
            // Get footer cell element.
            const cell = table.tFoot.rows[0].cells[column];

            // Set value into dynamic footer cell element.
            if (column === totals.length - 1) {
                // Percentage column uses the numerator and denominator,
                // and adapts to the number of decimal places.
                const match = /\.([0-9]+)/.exec(cell.textContent);
                const places = match ? match[1].length : 0;
                const { numer, denom } = totals[column];
                cell.dataset.ratio = `${numer} ${denom}`;
                // Check denom to prevent NaN if filtered files contain no statements
                cell.textContent = denom
                    ? `${(numer * 100 / denom).toFixed(places)}%`
                    : `${(100).toFixed(places)}%`;
            } else {
                cell.textContent = totals[column];
            }
        }
    }));

    // Trigger change event on setup, to force filter on page refresh
    // (filter value may still be present).
    document.getElementById("filter").dispatchEvent(new Event("change"));
};

// Loaded on index.html
coverage.index_ready = function ($) {
    // Look for a localStorage item containing previous sort settings:
    var sort_list = [];
    var storage_name = "COVERAGE_INDEX_SORT";
    var stored_list = undefined;
    try {
        stored_list = localStorage.getItem(storage_name);
    } catch(err) {}

    if (stored_list) {
        sort_list = JSON.parse('[[' + stored_list + ']]');
    }

    // Create a new widget which exists only to save and restore
    // the sort order:
    $.tablesorter.addWidget({
        id: "persistentSort",

        // Format is called by the widget before displaying:
        format: function (table) {
            if (table.config.sortList.length === 0 && sort_list.length > 0) {
                // This table hasn't been sorted before - we'll use
                // our stored settings:
                $(table).trigger('sorton', [sort_list]);
            }
            else {
                // This is not the first load - something has
                // already defined sorting so we'll just update
                // our stored value to match:
                sort_list = table.config.sortList;
            }
        }
    });

    // Configure our tablesorter to handle the variable number of
    // columns produced depending on report options:
    var headers = [];
    var col_count = $("table.index > thead > tr > th").length;

    headers[0] = { sorter: 'text' };
    for (i = 1; i < col_count-1; i++) {
        headers[i] = { sorter: 'digit' };
    }
    headers[col_count-1] = { sorter: 'percent' };

    // Enable the table sorter:
    $("table.index").tablesorter({
        widgets: ['persistentSort'],
        headers: headers
    });

    coverage.assign_shortkeys();
    coverage.wire_up_filter();

    // Watch for page unload events so we can save the final sort settings:
    $(window).on("unload", function () {
        try {
            localStorage.setItem(storage_name, sort_list.toString())
        } catch(err) {}
    });
};

// -- pyfile stuff --

coverage.LINE_FILTERS_STORAGE = "COVERAGE_LINE_FILTERS";

coverage.pyfile_ready = function ($) {
    // If we're directed to a particular line number, highlight the line.
    var frag = location.hash;
    if (frag.length > 2 && frag[1] === 't') {
        $(frag).addClass('highlight');
        coverage.set_sel(parseInt(frag.substr(2), 10));
    }
    else {
        coverage.set_sel(0);
    }

    $(document)
        .bind('keydown', 'j', coverage.to_next_chunk_nicely)
        .bind('keydown', 'k', coverage.to_prev_chunk_nicely)
        .bind('keydown', '0', coverage.to_top)
        .bind('keydown', '1', coverage.to_first_chunk)
        ;

    $(".button_toggle_run").click(function (evt) {coverage.toggle_lines(evt.target, "run");});
    $(".button_toggle_exc").click(function (evt) {coverage.toggle_lines(evt.target, "exc");});
    $(".button_toggle_mis").click(function (evt) {coverage.toggle_lines(evt.target, "mis");});
    $(".button_toggle_par").click(function (evt) {coverage.toggle_lines(evt.target, "par");});

    coverage.filters = undefined;
    try {
        coverage.filters = localStorage.getItem(coverage.LINE_FILTERS_STORAGE);
    } catch(err) {}

    if (coverage.filters) {
        coverage.filters = JSON.parse(coverage.filters);
    }
    else {
        coverage.filters = {run: false, exc: true, mis: true, par: true};
    }

    for (cls in coverage.filters) {
        coverage.set_line_visibilty(cls, coverage.filters[cls]);
    }

    coverage.assign_shortkeys();
    coverage.init_scroll_markers();

    // Rebuild scroll markers when the window height changes.
    $(window).resize(coverage.build_scroll_markers);
};

coverage.toggle_lines = function (btn, cls) {
    var onoff = !$(btn).hasClass("show_" + cls);
    coverage.set_line_visibilty(cls, onoff);
    coverage.build_scroll_markers();
    coverage.filters[cls] = onoff;
    try {
        localStorage.setItem(coverage.LINE_FILTERS_STORAGE, JSON.stringify(coverage.filters));
    } catch(err) {}
};

coverage.set_line_visibilty = function (cls, onoff) {
    var show = "show_" + cls;
    var btn = $(".button_toggle_" + cls);
    if (onoff) {
        $("#source ." + cls).addClass(show);
        btn.addClass(show);
    }
    else {
        $("#source ." + cls).removeClass(show);
        btn.removeClass(show);
    }
};

// Return the nth line div.
coverage.line_elt = function (n) {
    return $("#t" + n);
};

// Set the selection.  b and e are line numbers.
coverage.set_sel = function (b, e) {
    // The first line selected.
    coverage.sel_begin = b;
    // The next line not selected.
    coverage.sel_end = (e === undefined) ? b+1 : e;
};

coverage.to_top = function () {
    coverage.set_sel(0, 1);
    coverage.scroll_window(0);
};

coverage.to_first_chunk = function () {
    coverage.set_sel(0, 1);
    coverage.to_next_chunk();
};

// Return a string indicating what kind of chunk this line belongs to,
// or null if not a chunk.
coverage.chunk_indicator = function (line_elt) {
    var klass = line_elt.attr('class');
    if (klass) {
        var m = klass.match(/\bshow_\w+\b/);
        if (m) {
            return m[0];
        }
    }
    return null;
};

coverage.to_next_chunk = function () {
    var c = coverage;

    // Find the start of the next colored chunk.
    var probe = c.sel_end;
    var chunk_indicator, probe_line;
    while (true) {
        probe_line = c.line_elt(probe);
        if (probe_line.length === 0) {
            return;
        }
        chunk_indicator = c.chunk_indicator(probe_line);
        if (chunk_indicator) {
            break;
        }
        probe++;
    }

    // There's a next chunk, `probe` points to it.
    var begin = probe;

    // Find the end of this chunk.
    var next_indicator = chunk_indicator;
    while (next_indicator === chunk_indicator) {
        probe++;
        probe_line = c.line_elt(probe);
        next_indicator = c.chunk_indicator(probe_line);
    }
    c.set_sel(begin, probe);
    c.show_selection();
};

coverage.to_prev_chunk = function () {
    var c = coverage;

    // Find the end of the prev colored chunk.
    var probe = c.sel_begin-1;
    var probe_line = c.line_elt(probe);
    if (probe_line.length === 0) {
        return;
    }
    var chunk_indicator = c.chunk_indicator(probe_line);
    while (probe > 0 && !chunk_indicator) {
        probe--;
        probe_line = c.line_elt(probe);
        if (probe_line.length === 0) {
            return;
        }
        chunk_indicator = c.chunk_indicator(probe_line);
    }

    // There's a prev chunk, `probe` points to its last line.
    var end = probe+1;

    // Find the beginning of this chunk.
    var prev_indicator = chunk_indicator;
    while (prev_indicator === chunk_indicator) {
        probe--;
        probe_line = c.line_elt(probe);
        prev_indicator = c.chunk_indicator(probe_line);
    }
    c.set_sel(probe+1, end);
    c.show_selection();
};

// Return the line number of the line nearest pixel position pos
coverage.line_at_pos = function (pos) {
    var l1 = coverage.line_elt(1),
        l2 = coverage.line_elt(2),
        result;
    if (l1.length && l2.length) {
        var l1_top = l1.offset().top,
            line_height = l2.offset().top - l1_top,
            nlines = (pos - l1_top) / line_height;
        if (nlines < 1) {
            result = 1;
        }
        else {
            result = Math.ceil(nlines);
        }
    }
    else {
        result = 1;
    }
    return result;
};

// Returns 0, 1, or 2: how many of the two ends of the selection are on
// the screen right now?
coverage.selection_ends_on_screen = function () {
    if (coverage.sel_begin === 0) {
        return 0;
    }

    var top = coverage.line_elt(coverage.sel_begin);
    var next = coverage.line_elt(coverage.sel_end-1);

    return (
        (top.isOnScreen() ? 1 : 0) +
        (next.isOnScreen() ? 1 : 0)
    );
};

coverage.to_next_chunk_nicely = function () {
    coverage.finish_scrolling();
    if (coverage.selection_ends_on_screen() === 0) {
        // The selection is entirely off the screen: select the top line on
        // the screen.
        var win = $(window);
        coverage.select_line_or_chunk(coverage.line_at_pos(win.scrollTop()));
    }
    coverage.to_next_chunk();
};

coverage.to_prev_chunk_nicely = function () {
    coverage.finish_scrolling();
    if (coverage.selection_ends_on_screen() === 0) {
        var win = $(window);
        coverage.select_line_or_chunk(coverage.line_at_pos(win.scrollTop() + win.height()));
    }
    coverage.to_prev_chunk();
};

// Select line number lineno, or if it is in a colored chunk, select the
// entire chunk
coverage.select_line_or_chunk = function (lineno) {
    var c = coverage;
    var probe_line = c.line_elt(lineno);
    if (probe_line.length === 0) {
        return;
    }
    var the_indicator = c.chunk_indicator(probe_line);
    if (the_indicator) {
        // The line is in a highlighted chunk.
        // Search backward for the first line.
        var probe = lineno;
        var indicator = the_indicator;
        while (probe > 0 && indicator === the_indicator) {
            probe--;
            probe_line = c.line_elt(probe);
            if (probe_line.length === 0) {
                break;
            }
            indicator = c.chunk_indicator(probe_line);
        }
        var begin = probe + 1;

        // Search forward for the last line.
        probe = lineno;
        indicator = the_indicator;
        while (indicator === the_indicator) {
            probe++;
            probe_line = c.line_elt(probe);
            indicator = c.chunk_indicator(probe_line);
        }

        coverage.set_sel(begin, probe);
    }
    else {
        coverage.set_sel(lineno);
    }
};

coverage.show_selection = function () {
    var c = coverage;

    // Highlight the lines in the chunk
    $("#source .highlight").removeClass("highlight");
    for (var probe = c.sel_begin; probe > 0 && probe < c.sel_end; probe++) {
        c.line_elt(probe).addClass("highlight");
    }

    c.scroll_to_selection();
};

coverage.scroll_to_selection = function () {
    // Scroll the page if the chunk isn't fully visible.
    if (coverage.selection_ends_on_screen() < 2) {
        // Need to move the page. The html,body trick makes it scroll in all
        // browsers, got it from http://stackoverflow.com/questions/3042651
        var top = coverage.line_elt(coverage.sel_begin);
        var top_pos = parseInt(top.offset().top, 10);
        coverage.scroll_window(top_pos - 30);
    }
};

coverage.scroll_window = function (to_pos) {
    $("html,body").animate({scrollTop: to_pos}, 200);
};

coverage.finish_scrolling = function () {
    $("html,body").stop(true, true);
};

coverage.init_scroll_markers = function () {
    var c = coverage;
    // Init some variables
    c.lines_len = document.querySelectorAll('#source p').length;

    // Build html
    c.build_scroll_markers();
};

coverage.build_scroll_markers = function () {
    const temp_scroll_marker = document.getElementById('scroll_marker')
    if (temp_scroll_marker) temp_scroll_marker.remove();
    // Don't build markers if the window has no scroll bar.
    if (document.body.scrollHeight <= window.innerHeight) {
        return;
    }

    const marker_scale = window.innerHeight / document.body.scrollHeight;
    const line_height = clamp(window.innerHeight / coverage.lines_len, 3, 10);
    
    let previous_line = -99, last_mark, last_top;
    
    const scroll_marker = document.createElement("div");
    scroll_marker.id = "scroll_marker";
    document.getElementById('source').querySelectorAll(
        'p.show_run, p.show_mis, p.show_exc, p.show_exc, p.show_par'
    ).forEach(element => {
        const line_top = Math.floor(element.offsetTop * marker_scale);
        const line_number = parseInt(element.id.substr(1));

        if (line_number === previous_line + 1) {
            // If this solid missed block just make previous mark higher.
            last_mark.style.height = `${line_top + line_height - last_top}px`;
        } else {
            // Add colored line in scroll_marker block.
            last_mark = document.createElement("div");
            last_mark.id = `m${line_number}`;
            last_mark.classList.add("marker");
            last_mark.style.height = `${line_height}px`;
            last_mark.style.top = `${line_top}px`;
            scroll_marker.append(last_mark);
            last_top = line_top;
        }

        previous_line = line_number;
    });

    // Append last to prevent layout calculation
    document.body.append(scroll_marker);
};
