// To make the code more testable, we monkeypatch some of it.
$.extend(coverage, {
    line_elt: function(n) {
        return $(coverage.fixture + " .t" + n);
    },
    num_elt: function(n) {
        return $(coverage.fixture + " .n" + n);
    },
    scroll_to_selection: function() {}
});

// Test helpers

function selection_is(sel) {
    equals(coverage.sel_begin, sel[0]);
    equals(coverage.sel_end, sel[1]);
}

// Tests

$.each([
    ['rrwwrr', [1,3], [5,7]], 
    ['rb', [1,2], [2,3]],
    ['wrrwrrw', [2,4], [5,7]],
    ['rrrbbb', [1,4], [4,7]]
], function(i, params) {

    var id = params[0];
    var fixture = "#"+id;
    var c1 = params[1];
    var c2 = params[2];

    function setup() {
        coverage.fixture = fixture;
    };

    test("first chunk on line 1 "+id, function() {
        setup();
        coverage.to_first_chunk();
        selection_is(c1);
    });

    test("move to next chunk "+id, function() {
        setup();
        coverage.to_first_chunk();
        coverage.to_next_chunk();
        selection_is(c2);
    });

    test("move to first chunk "+id, function() {
        setup();
        coverage.to_first_chunk();
        coverage.to_next_chunk();
        coverage.to_first_chunk();
        selection_is(c1);
    });

    test("move to previous chunk "+id, function() {
        setup();
        coverage.to_first_chunk();
        coverage.to_next_chunk();
        coverage.to_prev_chunk();
        selection_is(c1);
    });

    test("next doesn't move after last chunk "+id, function() {
        setup();
        coverage.to_first_chunk();
        coverage.to_next_chunk();
        coverage.to_next_chunk();
        selection_is(c2);
    });

    test("prev doesn't move before first chunk "+id, function() {
        setup();
        coverage.to_first_chunk();
        coverage.to_next_chunk();
        coverage.to_prev_chunk();
        coverage.to_prev_chunk();
        selection_is(c1);
    });

});

test("jump from a line selected", function() {
    coverage.fixture = "#rrwwrr";
    coverage.set_sel(3, 4);
    coverage.to_next_chunk();
    selection_is([5,7]);
});
