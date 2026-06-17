/**
 * update-watch-habits-page.mjs
 *
 * Rewrites all 5 content visuals on the Watch Habits page with:
 *  - Aggregation wrapper on all Y/sort field references (fixes blank charts)
 *  - No stylePreset (fixes "Style preset not found" dialog)
 *  - Proper chart visualContainerObjects pattern matching existing pages
 *  - Data labels, axis formatting, centered titles
 */

import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const BASE = 'C:\\Users\\Owner\\Desktop\\Tyler\\OneDrive\\Projects\\Movies\\Movie BI';
const VISUALS = join(BASE, 'Movie Dashboard.Report', 'definition', 'pages', 'pgWatchHabits', 'visuals');
const SCHEMA  = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.10.0/schema.json';

// ── Field helpers ─────────────────────────────────────────────────────────────

/** Category axis field (Column, no aggregation, active=true) */
function catProj(entity, property) {
  return {
    field: { Column: { Expression: { SourceRef: { Entity: entity } }, Property: property } },
    queryRef: `${entity}.${property}`,
    nativeQueryRef: property,
    active: true,
  };
}

/** Y-axis / value field using Aggregation wrapper.
 *  fn: 0=Sum, 1=Avg, 2=CountNonNull, 3=Min, 4=Max */
function aggProj(entity, property, fn, queryRef, nativeRef, displayName) {
  const p = {
    field: {
      Aggregation: {
        Expression: { Column: { Expression: { SourceRef: { Entity: entity } }, Property: property } },
        Function: fn,
      },
    },
    queryRef,
    nativeQueryRef: nativeRef,
  };
  if (displayName) p.displayName = displayName;
  return p;
}

/** Aggregation field object (used in sortDefinition.sort) */
function aggSortField(entity, property, fn) {
  return {
    Aggregation: {
      Expression: { Column: { Expression: { SourceRef: { Entity: entity } }, Property: property } },
      Function: fn,
    },
  };
}

/** Column field object (used in sortDefinition.sort when sorting by category) */
function colSortField(entity, property) {
  return { Column: { Expression: { SourceRef: { Entity: entity } }, Property: property } };
}

// ── visualContainerObjects pattern (chart visuals — no stylePreset!) ───────────

function chartVco(titleText, padding = { top: 5, bottom: 0, left: 5, right: 0 }) {
  return {
    title: [{
      properties: {
        text:      { expr: { Literal: { Value: `'${titleText}'` } } },
        titleWrap: { expr: { Literal: { Value: 'true' } } },
        alignment: { expr: { Literal: { Value: "'center'" } } },
        fontSize:  { expr: { Literal: { Value: '14D' } } },
      },
    }],
    visualHeader: [{ properties: { show: { expr: { Literal: { Value: 'false' } } } } }],
    background: [{
      properties: {
        show:         { expr: { Literal: { Value: 'true' } } },
        color:        { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
        transparency: { expr: { Literal: { Value: '100D' } } },
      },
    }],
    visualTooltip: [{
      properties: {
        titleFontColor:       { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
        valueFontColor:       { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
        background:           { solid: { color: { expr: { Literal: { Value: "'#31394C'" } } } } },
        actionFontColor:      { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
        themedTitleFontColor: { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
        themedValueFontColor: { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
      },
    }],
    visualHeaderTooltip: [{
      properties: {
        themedTitleFontColor: { solid: { color: { expr: { Literal: { Value: "'#FFFFFF'" } } } } },
      },
    }],
    padding: [{
      properties: {
        top:    { expr: { Literal: { Value: `${padding.top}D` } } },
        bottom: { expr: { Literal: { Value: `${padding.bottom}D` } } },
        left:   { expr: { Literal: { Value: `${padding.left}D` } } },
        right:  { expr: { Literal: { Value: `${padding.right}D` } } },
      },
    }],
  };
}

/** Standard bar/column axis objects */
function barObjects(catWidth = 20, maxMargin = 50, catFontSize = 9) {
  return {
    labels: [{
      properties: {
        show:          { expr: { Literal: { Value: 'true' } } },
        labelPosition: { expr: { Literal: { Value: "'OutsideEnd'" } } },
        labelDensity:  { expr: { Literal: { Value: '100L' } } },
        optimizeLabelDisplay: { expr: { Literal: { Value: 'false' } } },
        labelContainerMaxWidth: { expr: { Literal: { Value: '199D' } } },
        fontSize:      { expr: { Literal: { Value: '9D' } } },
      },
    }],
    categoryAxis: [{
      properties: {
        preferredCategoryWidth: { expr: { Literal: { Value: `${catWidth}D` } } },
        maxMarginFactor:        { expr: { Literal: { Value: `${maxMargin}L` } } },
        concatenateLabels:      { expr: { Literal: { Value: 'true' } } },
        fontSize:               { expr: { Literal: { Value: `${catFontSize}D` } } },
        showAxisTitle:          { expr: { Literal: { Value: 'false' } } },
      },
    }],
    valueAxis: [{
      properties: {
        fontSize:      { expr: { Literal: { Value: '9D' } } },
        showAxisTitle: { expr: { Literal: { Value: 'false' } } },
      },
    }],
  };
}

// ── Write helper ──────────────────────────────────────────────────────────────

function write(name, json) {
  const dir = join(VISUALS, name);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, 'visual.json'), JSON.stringify(json, null, 2), 'utf8');
  console.log(`✔ ${name}`);
}

// ═════════════════════════════════════════════════════════════════════════════
//  CONTENT VISUALS
// ═════════════════════════════════════════════════════════════════════════════

// ── v01DonutLocation ──────────────────────────────────────────────────────────
// Where do you watch? — count of movies by Watch Location
write('v01DonutLocation', {
  $schema: SCHEMA,
  name: 'v01DonutLocation',
  position: { x: 320, y: 30, z: 1000, width: 385, height: 390, tabOrder: 100 },
  visual: {
    visualType: 'donutChart',
    query: {
      queryState: {
        Category: { projections: [catProj('Movie Rankings', 'Watch Location')] },
        Y: { projections: [aggProj('Movie Rankings', 'Movie', 2,
               'CountNonNull(Movie Rankings.Movie)', '# Movies', '# Movies')] },
      },
      sortDefinition: {
        sort: [{ field: aggSortField('Movie Rankings', 'Movie', 2), direction: 'Descending' }],
        isDefaultSort: true,
      },
    },
    objects: {
      legend: [{
        properties: {
          show:     { expr: { Literal: { Value: 'true' } } },
          position: { expr: { Literal: { Value: "'Right'" } } },
          fontSize: { expr: { Literal: { Value: '10D' } } },
        },
      }],
      labels: [{
        properties: {
          show:     { expr: { Literal: { Value: 'true' } } },
          fontSize: { expr: { Literal: { Value: '10D' } } },
        },
      }],
    },
    visualContainerObjects: chartVco('Watch Location'),
    drillFilterOtherVisuals: true,
  },
});

// ── v02BarWatchedWith ─────────────────────────────────────────────────────────
// Who do you watch with? — count of movies by Watched With
write('v02BarWatchedWith', {
  $schema: SCHEMA,
  name: 'v02BarWatchedWith',
  position: { x: 720, y: 30, z: 2000, width: 430, height: 390, tabOrder: 200 },
  visual: {
    visualType: 'clusteredBarChart',
    query: {
      queryState: {
        Category: { projections: [catProj('Movie Rankings', 'Watched With')] },
        Y: { projections: [aggProj('Movie Rankings', 'Movie', 2,
               'CountNonNull(Movie Rankings.Movie)', '# Movies', '# Movies')] },
      },
      sortDefinition: {
        sort: [{ field: aggSortField('Movie Rankings', 'Movie', 2), direction: 'Descending' }],
        isDefaultSort: true,
      },
    },
    objects: barObjects(20, 50, 9),
    visualContainerObjects: chartVco('Who Do You Watch With?'),
    drillFilterOtherVisuals: true,
  },
});

// ── v03BarRewatched ───────────────────────────────────────────────────────────
// Rewatched movies — Sum of Times Watched, sorted desc (repeat watches float top)
write('v03BarRewatched', {
  $schema: SCHEMA,
  name: 'v03BarRewatched',
  position: { x: 1165, y: 30, z: 3000, width: 405, height: 390, tabOrder: 300 },
  visual: {
    visualType: 'clusteredBarChart',
    query: {
      queryState: {
        Category: { projections: [catProj('Movie Rankings', 'Movie')] },
        Y: { projections: [aggProj('Movie Rankings', 'Times Watched', 0,
               'Sum(Movie Rankings.Times Watched)', 'Times Watched', 'Times Watched')] },
      },
      sortDefinition: {
        sort: [{ field: aggSortField('Movie Rankings', 'Times Watched', 0), direction: 'Descending' }],
        isDefaultSort: true,
      },
    },
    objects: barObjects(20, 50, 9),
    visualContainerObjects: chartVco('Times Watched'),
    drillFilterOtherVisuals: true,
  },
});

// ── v04BarLanguage ────────────────────────────────────────────────────────────
// Movies by language — how international is your taste?
write('v04BarLanguage', {
  $schema: SCHEMA,
  name: 'v04BarLanguage',
  position: { x: 320, y: 440, z: 4000, width: 540, height: 430, tabOrder: 400 },
  visual: {
    visualType: 'clusteredBarChart',
    query: {
      queryState: {
        Category: { projections: [catProj('Movie Rankings', 'Language')] },
        Y: { projections: [aggProj('Movie Rankings', 'Movie', 2,
               'CountNonNull(Movie Rankings.Movie)', '# Movies', '# Movies')] },
      },
      sortDefinition: {
        sort: [{ field: aggSortField('Movie Rankings', 'Movie', 2), direction: 'Descending' }],
        isDefaultSort: true,
      },
    },
    objects: {
      ...barObjects(20, 50, 9),
      // tighter bar spacing for language list
      spacing: [{ properties: { verticalSpacing: { expr: { Literal: { Value: '0D' } } } } }],
    },
    visualContainerObjects: chartVco('Movies by Language'),
    drillFilterOtherVisuals: true,
  },
});

// ── v05ColumnYear ─────────────────────────────────────────────────────────────
// Movies by release year — what era of cinema do you watch?
write('v05ColumnYear', {
  $schema: SCHEMA,
  name: 'v05ColumnYear',
  position: { x: 875, y: 440, z: 5000, width: 695, height: 430, tabOrder: 500 },
  visual: {
    visualType: 'clusteredColumnChart',
    query: {
      queryState: {
        Category: { projections: [catProj('Movie Rankings', 'Year')] },
        Y: { projections: [aggProj('Movie Rankings', 'Movie', 2,
               'CountNonNull(Movie Rankings.Movie)', '# Movies', '# Movies')] },
      },
      // Sort by Year ascending (chronological)
      sortDefinition: {
        sort: [{ field: colSortField('Movie Rankings', 'Year'), direction: 'Ascending' }],
        isDefaultSort: true,
      },
    },
    objects: {
      labels: [{
        properties: {
          show:    { expr: { Literal: { Value: 'true' } } },
          fontSize: { expr: { Literal: { Value: '9D' } } },
        },
      }],
      categoryAxis: [{
        properties: {
          preferredCategoryWidth: { expr: { Literal: { Value: '55D' } } },
          fontSize:               { expr: { Literal: { Value: '9D' } } },
          maxMarginFactor:        { expr: { Literal: { Value: '15L' } } },
          show:                   { expr: { Literal: { Value: 'true' } } },
          showAxisTitle:          { expr: { Literal: { Value: 'false' } } },
        },
      }],
      valueAxis: [{
        properties: {
          show:          { expr: { Literal: { Value: 'true' } } },
          showAxisTitle: { expr: { Literal: { Value: 'false' } } },
          fontSize:      { expr: { Literal: { Value: '9D' } } },
        },
      }],
      // Avg reference line (uses the existing Avg measure from Movie Rankings)
      y1AxisReferenceLine: [{
        properties: {
          show:        { expr: { Literal: { Value: 'false' } } },
          displayName: { expr: { Literal: { Value: "'Avg'" } } },
          style:       { expr: { Literal: { Value: "'dotted'" } } },
          position:    { expr: { Literal: { Value: "'back'" } } },
          width:       { expr: { Literal: { Value: '1D' } } },
          lineColor:   { solid: { color: { expr: { Literal: { Value: "'#018DA2'" } } } } },
        },
        selector: { id: '1' },
      }],
    },
    visualContainerObjects: chartVco('Movies by Release Year'),
    drillFilterOtherVisuals: true,
  },
});

console.log('\n✅  Watch Habits content visuals updated!');
console.log('   → Close Power BI Desktop, reopen Movie Dashboard.pbip, navigate to Watch Habits');
