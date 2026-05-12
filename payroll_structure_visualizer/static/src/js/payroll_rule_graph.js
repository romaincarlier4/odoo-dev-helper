/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const STRUCTURE_COLORS = [
    "#4361ee", "#7209b7", "#e63946", "#2a9d8f", "#e76f51",
    "#457b9d", "#6a4c93", "#1982c4", "#8ac926", "#ff595e",
];

export class PayrollRuleGraph extends Component {
    static template = "payroll_structure_visualizer.RuleGraph";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            loading: true,
            structures: [],
            structureColors: {},
            selectedRuleCode: null,   // highlight all cards sharing this code
            filterText: "",
            showSharedOnly: false,
        });
        onWillStart(() => this._loadData());
    }

    async _loadData() {
        const [structures, rules] = await Promise.all([
            this.orm.searchRead(
                "hr.payroll.structure",
                [],
                ["id", "name", "type_id"],
                { order: "name asc" }
            ),
            this.orm.searchRead(
                "hr.salary.rule",
                [["active", "=", true]],
                ["id", "name", "code", "struct_ids", "struct_count", "is_shared", "sequence"],
                { order: "sequence asc, id asc" }
            ),
        ]);

        const rulesByStruct = {};
        for (const rule of rules) {
            for (const sid of rule.struct_ids) {
                (rulesByStruct[sid] ||= []).push(rule);
            }
        }

        const structureColors = {};
        structures.forEach((s, i) => {
            structureColors[s.id] = STRUCTURE_COLORS[i % STRUCTURE_COLORS.length];
            s.rules = (rulesByStruct[s.id] || []).slice().sort(
                (a, b) => a.sequence - b.sequence || a.id - b.id
            );
        });

        this._allRules = rules;
        this.state.structures = structures;
        this.state.structureColors = structureColors;
        this.state.loading = false;
    }

    get filteredStructures() {
        const text = this.state.filterText.trim().toLowerCase();
        const onlyShared = this.state.showSharedOnly;

        return this.state.structures
            .map((s) => ({
                ...s,
                rules: s.rules.filter(
                    (r) =>
                        (!onlyShared || r.is_shared) &&
                        (!text ||
                            r.code.toLowerCase().includes(text) ||
                            r.name.toLowerCase().includes(text))
                ),
            }))
            .filter((s) => s.rules.length > 0);
    }

    get selectedRule() {
        if (!this.state.selectedRuleCode) return null;
        return this._allRules.find((r) => r.code === this.state.selectedRuleCode) || null;
    }

    get selectedRuleStructures() {
        const rule = this.selectedRule;
        if (!rule) return [];
        return this.state.structures.filter((s) =>
            rule.struct_ids.includes(s.id)
        );
    }

    isRuleHighlighted(rule) {
        return this.state.selectedRuleCode === rule.code;
    }

    isRuleDimmed(rule) {
        return this.state.selectedRuleCode !== null &&
               this.state.selectedRuleCode !== rule.code;
    }

    selectRule(rule) {
        if (!rule.is_shared) return;
        this.state.selectedRuleCode =
            this.state.selectedRuleCode === rule.code ? null : rule.code;
    }

    clearSelection() {
        this.state.selectedRuleCode = null;
    }

    onSearchInput(ev) {
        this.state.filterText = ev.target.value;
    }

    toggleSharedOnly() {
        this.state.showSharedOnly = !this.state.showSharedOnly;
    }

    colorOf(structId) {
        return this.state.structureColors[structId] || "#adb5bd";
    }

    hex2rgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r},${g},${b},${alpha})`;
    }
}

registry.category("actions").add("payroll_rule_graph", PayrollRuleGraph);
