import js from "@eslint/js";
import globals from "globals";

export default [
	{
		ignores: [
			"compendium/public/dist/**",
			"compendium/templates/includes/**",
			"compendium/public/js/lib/**",
			"node_modules/**",
		],
	},
	js.configs.recommended,
	{
		languageOptions: {
			ecmaVersion: "latest",
			sourceType: "module",
			globals: {
				...globals.browser,
				...globals.node,
				compendium: true,
				frappe: true,
				__: true,
				locals: true,
				cint: true,
				cstr: true,
				cur_frm: true,
				cur_dialog: true,
				cur_page: true,
				cur_list: true,
				flt: true,
				$: true,
				jQuery: true,
				moment: true,
				hljs: true,
			},
		},
		rules: {
			// Recommended rules that fire on established Frappe/Desk idioms.
			"no-useless-escape": "off",
			"no-unused-vars": "off",
			"no-extra-boolean-cast": "off",
			"no-control-regex": "off",
			"no-console": "warn",
		},
	},
	{
		files: ["cypress/**/*.js"],
		languageOptions: {
			globals: {
				...globals.mocha,
				cy: true,
				Cypress: true,
			},
		},
	},
];
