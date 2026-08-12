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
		cy.get(".docs-page-roles").should("contain", "System Manager");
		cy.get(".docs-page-roles").should("contain", "because you have");
	});

	it("renders a TOC and follows heading deep links", () => {
		cy.viewport(1280, 720);
		cy.visit("/app/docs/en/compendium/docs/authoring#role-defaults");
		cy.get(".docs-toc-pane").should("be.visible");
		cy.get('.docs-toc-pane a[href="#role-defaults"]').should("exist");
		cy.location("hash").should("eq", "#role-defaults");
		cy.get(".docs-reading-pane h2#role-defaults").should("be.visible");
	});

	it("shows not-found state for missing pages", () => {
		cy.visit("/app/docs/en/does-not-exist-page");
		cy.get(".docs-state").should("not.have.class", "hide");
		cy.get(".docs-reading-pane").should("have.class", "hide");
		cy.get(".docs-state-content").should("contain", "could not find");
	});
});
