// Tests of coverage.py HTML report chunk navigation.

// Test helpers

function selection_is(sel) {
    var beg = sel[0], end = sel[1];
    equals(coverage.sel_begin, beg);
    equals(coverage.sel_end, end);
    equals(coverage.code_container().find(".highlight").length, end-beg);
}

function build_fixture(spec) {
    $("#fixture-template").tmpl().appendTo("#qunit-fixture");
    for (var i = 0; i < spec.length; i++) {
        var data = {number: i+1, klass: spec.substr(i, 1)};
        $("#lineno-template").tmpl(data).appendTo("#qunit-fixture .linenos");
        $("#text-template").tmpl(data).appendTo("#qunit-fixture .text");
    }
    coverage.pyfile_ready(jQuery);
}

// Tests

// Zero-chunk tests

module("Zero-chunk navigation", {
    setup: function() {
        build_fixture("wwww");
    }
});

test("set_sel defaults", function() {
    coverage.set_sel(2);
    equals(coverage.sel_begin, 2);
    equals(coverage.sel_end, 3);
});

test("No first chunk to select", function() {
    coverage.to_first_chunk();
});

// One-chunk tests

$.each([
    ['rrrrr', [1,6]],
    ['r', [1,2]],
    ['wwrrrr', [3,7]],
    ['wwrrrrww', [3,7]],
    ['rrrrww', [1,5]]
], function(i, params) {

    // Each of these tests uses a fixture with one highlighted chunks.
    var id = params[0];
    var c1 = params[1];

    module("One-chunk navigation - " + id, {
        setup: function() {
            build_fixture(id);
        }
    });

    test("First chunk", function() {
        coverage.to_first_chunk();
        selection_is(c1);
    });

    test("Next chunk is first chunk", function() {
        coverage.to_next_chunk();
        selection_is(c1);
    });

    test("There is no next chunk", function() {
        coverage.to_first_chunk();
        coverage.to_next_chunk();
        selection_is(c1);
    });

    test("There is no prev chunk", function() {
        coverage.to_first_chunk();
        coverage.to_prev_chunk();
        selection_is(c1);
    });
});

// Two-chunk tests

$.each([
    ['rrwwrrrr', [1,3], [5,9]],
    ['rb', [1,2], [2,3]],
    ['rbbbbbbbbbb', [1,2], [2,12]],
    ['rrrrrrrrrrb', [1,11], [11,12]],
    ['wrrwrrrrw', [2,4], [5,9]],
    ['rrrbbb', [1,4], [4,7]]
], function(i, params) {

    // Each of these tests uses a fixture with two highlighted chunks.
    var id = params[0];
    var c1 = params[1];
    var c2 = params[2];

    module("Two-chunk navigation - " + id, {
        setup: function() {
            build_fixture(id);
        }
    });

    test("First chunk", function() {
        coverage.to_first_chunk();
        selection_is(c1);
    });

    test("Next chunk is first chunk", function() {
        coverage.to_next_chunk();
        selection_is(c1);
    });

    test("Move to next chunk", function() {
        coverage.to_first_chunk();
        coverage.to_next_chunk();
        selection_is(c2);
    });

    test("Move to first chunk", function() {
        coverage.to_first_chunk();
        coverage.to_next_chunk();
        coverage.to_first_chunk();
        selection_is(c1);
    });

    test("Move to previous chunk", function() {
        coverage.to_first_chunk();
        coverage.to_next_chunk();
        coverage.to_prev_chunk();
        selection_is(c1);
    });

    test("Next doesn't move after last chunk", function() {
        coverage.to_first_chunk();
        coverage.to_next_chunk();
        coverage.to_next_chunk();
        selection_is(c2);
    });

    test("Prev doesn't move before first chunk", function() {
        coverage.to_first_chunk();
        coverage.to_next_chunk();
        coverage.to_prev_chunk();
        coverage.to_prev_chunk();
        selection_is(c1);
    });

});

module("Miscellaneous");

test("Jump from a line selected", function() {
    build_fixture("rrwwrr");
    coverage.set_sel(3);
    coverage.to_next_chunk();
    selection_is([5,7]);
});
