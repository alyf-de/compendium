context("Documentation Browser", () => {
	before(() => {
		cy.login();
	});

	it("opens the docs page and loads the first accessible page", () => {
		cy.visit("/app/docs");
		cy.location("pathname").should("match", /\/app\/docs\/[a-z]{2}(-[A-Z]{2})?/);
		cy.get(".docs-tree .docs-tree-node").should("have.length.at.least", 1);
		cy.get(".docs-reading-pane").should("not.have.class", "hide");
		cy.get(".docs-reading-pane").should("contain", "Compendium");
	});

	it("navigates nested documentation routes", () => {
		cy.visit("/app/docs/en/compendium/docs/authoring");
		cy.get('.docs-tree-node.active[data-path="compendium/docs/authoring"]').should("exist");
		cy.get(".docs-reading-pane").contains("Authoring Guide");
		cy.get(".navbar-breadcrumbs li").first().should("contain", "Documentation");
		cy.get(".navbar-breadcrumbs li").last().should("contain", "Authoring Guide");
	});

	it("collapses and expands sidebar groups", () => {
		cy.visit("/app/docs/en/compendium/docs/authoring");
		// Active path ancestors are expanded; sibling groups stay collapsed.
		cy.get('.docs-tree-item[data-path="compendium"]').should("not.have.class", "collapsed");
		cy.get(
			'.docs-tree-item[data-path="compendium"] > .docs-tree-row .docs-tree-toggle'
		).click();
		cy.get('.docs-tree-item[data-path="compendium"]').should("have.class", "collapsed");
		cy.get('.docs-tree-item[data-path="compendium"] > .docs-tree-children').should(
			"not.be.visible"
		);
		cy.get(
			'.docs-tree-item[data-path="compendium"] > .docs-tree-row .docs-tree-toggle'
		).click();
		cy.get('.docs-tree-item[data-path="compendium"]').should("not.have.class", "collapsed");
	});

	it("renders mermaid diagrams from fenced blocks", () => {
		cy.visit("/app/docs/en/compendium/docs/authoring");
		cy.get(".docs-reading-pane .mermaid svg", { timeout: 15000 }).should("exist");
	});

	it("highlights fenced code blocks", () => {
		cy.visit("/app/docs/en/compendium/docs/authoring");
		cy.get(".docs-reading-pane pre code.hljs", { timeout: 15000 }).should(
			"have.length.at.least",
			1
		);
	});

	it("shows which of the user's roles grant access", () => {
		cy.visit("/app/docs/en/compendium/docs/authoring");
		cy.get(".docs-page-footer").should("contain", "System Manager");
		cy.get(".docs-page-footer").should("contain", "because you have");
	});

	it("renders a TOC and follows heading deep links", () => {
		cy.viewport(1280, 720);
		// Heading after a Mermaid block: scroll must wait for SVG layout.
		cy.visit("/app/docs/en/compendium/docs/authoring#code-blocks");
		cy.get(".docs-toc-pane").should("be.visible");
		cy.get('.docs-toc-pane a[href="#code-blocks"]').should("exist");
		cy.location("hash").should("eq", "#code-blocks");
		cy.get(".docs-reading-pane .mermaid svg", { timeout: 15000 }).should("exist");
		cy.get(".docs-reading-pane h2#code-blocks").should(($heading) => {
			const heading_top = $heading[0].getBoundingClientRect().top;
			const pane_top = document
				.querySelector(".layout-main-section-wrapper")
				.getBoundingClientRect().top;
			expect(heading_top).to.be.closeTo(pane_top, 48);
		});

		cy.get('.docs-toc-pane a[href="#mermaid-diagrams"]').click();
		cy.location("pathname").should("eq", "/app/docs/en/compendium/docs/authoring");
		cy.location("hash").should("eq", "#mermaid-diagrams");
		cy.get(".docs-reading-pane h2#mermaid-diagrams").should("be.visible");
	});

	it("copies a heading deep link from the muted link icon", () => {
		cy.visit("/app/docs/en/compendium/docs/authoring");
		cy.window().then((win) => {
			cy.stub(win.navigator.clipboard, "writeText").as("clipboardWrite").resolves();
		});
		cy.get(".docs-reading-pane h2#code-blocks .docs-heading-anchor").should("exist").click();
		cy.get("@clipboardWrite").should("have.been.calledWithMatch", /#code-blocks$/);
	});

	it("shows Edit on GitHub for Administrator when repository is set", () => {
		cy.visit("/app/docs/en/compendium/docs/authoring");
		cy.get(".docs-page-footer .docs-edit-link")
			.should("be.visible")
			.and("contain", "Edit on GitHub")
			.and("have.attr", "href")
			.and("include", "github.com/alyf-de/compendium");
	});

	it("shows not-found state for missing pages", () => {
		cy.visit("/app/docs/en/does-not-exist-page");
		cy.get(".docs-state").should("not.have.class", "hide");
		cy.get(".docs-reading-pane").should("have.class", "hide");
		cy.get(".docs-state-content").should("contain", "could not find");
	});
});
