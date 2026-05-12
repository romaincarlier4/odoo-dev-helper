/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class PayrollStructureVisualizer extends Component {
    static template = "payroll_structure_visualizer.Visualizer";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            loading: true,
            structures: [],
            expandedIds: new Set(),
            selectedRuleId: null,
            selectedRule: null,
            filterText: "",
            showOnlyShared: false,
        });
        onWillStart(() => this._loadData());
    }

    async _loadData() {
        const [structures, rules] = await Promise.all([
            this.orm.searchRead(
                "hr.payroll.structure",
                [],
                ["id", "name", "type_id", "country_id", "rule_count", "shared_rule_count"],
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
            for (const structId of rule.struct_ids) {
                (rulesByStruct[structId] ||= []).push(rule);
            }
        }

        for (const struct of structures) {
            struct.rules = rulesByStruct[struct.id] || [];
        }

        this.allStructures = structures;
        this.state.structures = structures;
        this.state.loading = false;
    }

    get filteredStructures() {
        const text = this.state.filterText.trim().toLowerCase();
        const onlyShared = this.state.showOnlyShared;

        return this.state.structures
            .map((struct) => {
                const rules = struct.rules.filter(
                    (r) =>
                        (!onlyShared || r.is_shared) &&
                        (!text ||
                            r.name.toLowerCase().includes(text) ||
                            r.code.toLowerCase().includes(text))
                );
                return { ...struct, rules };
            })
            .filter((struct) => !text && !onlyShared || struct.rules.length > 0);
    }

    isExpanded(structId) {
        return this.state.expandedIds.has(structId);
    }

    toggleExpand(structId) {
        if (this.state.expandedIds.has(structId)) {
            this.state.expandedIds.delete(structId);
        } else {
            this.state.expandedIds.add(structId);
        }
    }

    expandAll() {
        for (const s of this.state.structures) {
            this.state.expandedIds.add(s.id);
        }
    }

    collapseAll() {
        this.state.expandedIds.clear();
    }

    selectRule(rule) {
        if (this.state.selectedRuleId === rule.id) {
            this.state.selectedRuleId = null;
            this.state.selectedRule = null;
        } else {
            this.state.selectedRuleId = rule.id;
            this.state.selectedRule = rule;
        }
    }

    clearSelection() {
        this.state.selectedRuleId = null;
        this.state.selectedRule = null;
    }

    isRuleSelected(ruleId) {
        return this.state.selectedRuleId === ruleId;
    }

    structHasSelectedRule(struct) {
        return (
            this.state.selectedRuleId !== null &&
            struct.rules.some((r) => r.id === this.state.selectedRuleId)
        );
    }

    structIsDimmed(struct) {
        return (
            this.state.selectedRuleId !== null &&
            !struct.rules.some((r) => r.id === this.state.selectedRuleId)
        );
    }

    get selectedRuleStructures() {
        if (!this.state.selectedRule) return [];
        return this.allStructures.filter((s) =>
            s.rules.some((r) => r.id === this.state.selectedRuleId)
        );
    }

    onSearchInput(ev) {
        this.state.filterText = ev.target.value;
    }

    toggleSharedFilter() {
        this.state.showOnlyShared = !this.state.showOnlyShared;
    }
}

registry.category("actions").add("payroll_structure_visualizer", PayrollStructureVisualizer);
