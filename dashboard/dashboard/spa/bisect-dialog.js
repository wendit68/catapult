/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import './cp-input.js';
import './cp-loading.js';
import './cp-radio-group.js';
import './cp-radio.js';
import './error-set.js';
import './raised-button.js';
import NewPinpointRequest from './new-pinpoint-request.js';
import {ElementBase, STORE} from './element-base.js';
import {UPDATE} from './simple-redux.js';
import {html, css} from 'lit-element';
import {isElementChildOf, pinpointJob} from './utils.js';

// Display a warning when bisecting large revision ranges.
const MANY_REVISIONS = 100;

export default class BisectDialog extends ElementBase {
  static get is() { return 'bisect-dialog'; }

  static get properties() {
    return {
      statePath: String,

      alertKeys: Array,
      able: Boolean,
      tooltip: String,
      errors: Array,
      isLoading: Boolean,
      isOpen: Boolean,
      jobId: String,
      bugId: String,
      patch: String,
      suite: String,
      measurement: String,
      bot: String,
      case: String,
      statistic: String,
      mode: String,
      startRevision: Number,
      endRevision: Number,
    };
  }

  static buildState(options = {}) {
    return {
      alertKeys: options.alertKeys || [],
      able: options.able || true,
      tooltip: options.tooltip || '',
      errors: [],
      isLoading: false,
      isOpen: false,
      jobId: '',
      bugId: options.bugId || '',
      patch: options.patch || '',
      suite: options.suite || '',
      measurement: options.measurement || '',
      bot: options.bot || '',
      case: options.case || '',
      statistic: options.statistic || '',
      mode: options.mode || BisectDialog.MODE.PERFORMANCE,
      startRevision: options.startRevision || 0,
      endRevision: options.endRevision || 0,
    };
  }

  static get styles() {
    return css`
      :host {
        position: relative;
      }

      #dialog {
        background: var(--background-color, white);
        box-shadow: var(--elevation-2);
        flex-direction: column;
        outline: none;
        padding: 16px;
        position: absolute;
        bottom: 0;
        z-index: var(--layer-menu, 100);
      }
      cp-input {
        margin: 12px 4px 4px 4px;
        width: 100px;
      }
      cp-radio-group {
        margin-left: 8px;
        flex-direction: row;
      }
      .row raised-button {
        flex-grow: 1;
      }
      .row {
        display: flex;
        align-items: center;
      }
      .warning {
        color: var(--error-color, red);
      }
      #cancel {
        background: var(--background-color, white);
        box-shadow: none;
      }
    `;
  }

  render() {
    return html`
      <raised-button
          id="open"
          ?disabled="${!this.able}"
          title="${this.tooltip}"
          @click="${this.onOpen_}">
        Bisect ${this.startRevision} - ${this.endRevision}
      </raised-button>

      <error-set .errors="${this.errors}"></error-set>
      <cp-loading ?loading="${this.isLoading}">
      </cp-loading>
      ${!this.jobId ? '' : html`
        <a target="_blank" href="${pinpointJob(this.jobId)}">${this.jobId}</a>
      `}

      <div id="dialog" ?hidden="${!this.isOpen}">
        <table>
          <tr>
            <td>Suite</td>
            <td>${this.suite}</td
          </tr>
          <tr>
            <td>Bot</td>
            <td>${this.bot}</td>
          </tr>
          <tr>
            <td>Measurement</td>
            <td>${this.measurement}</td>
          </tr>
          ${!this.case ? '' : html`
            <tr>
              <td>Case</td>
              <td>${this.case}</td>
            </tr>
          `}
          ${!this.statistic ? '' : html`
            <tr>
              <td>Statistic</td>
              <td>${this.statistic}</td>
            </tr>
          `}
        </table>

        <div class="row">
          <cp-input
              id="start_revision"
              label="Start Revision"
              tabindex="0"
              .value="${this.startRevision}"
              @change="${this.onStartRevision_}">
          </cp-input>

          <cp-input
              id="end_revision"
              label="End Revision"
              tabindex="0"
              .value="${this.endRevision}"
              @change="${this.onEndRevision_}">
          </cp-input>
        </div>

        <div class="row">
          <cp-input
              id="bug_id"
              label="Bug ID"
              tabindex="0"
              .value="${this.bugId}"
              @change="${this.onBugId_}">
          </cp-input>

          <cp-input
              id="patch"
              label="Patch"
              title="optional patch to apply to the entire job"
              tabindex="0"
              .value="${this.patch}"
              @change="${this.onPatch_}">
          </cp-input>
        </div>

        <div class="row">
          Mode:
          <cp-radio-group
              id="mode"
              selected="${this.mode}"
              @selected-changed="${this.onModeChange_}">
            <cp-radio name="performance">
              Performance
            </cp-radio>
            <cp-radio name="functional">
              Functional
            </cp-radio>
          </cp-radio-group>
        </div>

        ${((this.endRevision - this.startRevision) < MANY_REVISIONS) ? '' :
    html`
          <div class="row warning">
            Warning: bisect large revision ranges is slow and expensive.
          </div>
        `}

        <div class="row">
          <raised-button
              id="cancel"
              @click="${this.onCancel_}"
              tabindex="0">
            Cancel
          </raised-button>
          <raised-button
              id="start"
              @click="${this.onSubmit_}"
              tabindex="0">
            Start
          </raised-button>
        </div>
      </div>
    `;
  }

  firstUpdated() {
    this.addEventListener('blur', this.onBlur_.bind(this));
    this.addEventListener('keyup', this.onKeyup_.bind(this));
  }

  stateChanged(rootState) {
    super.stateChanged(rootState);

    if (this.isOpen) {
      this.shadowRoot.querySelector('#cancel').focus();
    }
  }

  async onKeyup_(event) {
    if (event.key === 'Escape') {
      await STORE.dispatch(UPDATE(this.statePath, {isOpen: false}));
    }
  }

  async onBlur_(event) {
    if (event.relatedTarget === this ||
        isElementChildOf(event.relatedTarget, this)) {
      return;
    }
    await STORE.dispatch(UPDATE(this.statePath, {isOpen: false}));
  }

  async onCancel_(event) {
    await STORE.dispatch(UPDATE(this.statePath, {isOpen: false}));
  }

  async onStartRevision_(event) {
    await STORE.dispatch(UPDATE(this.statePath, {
      startRevision: event.detail.value,
    }));
  }

  async onEndRevision_(event) {
    await STORE.dispatch(UPDATE(this.statePath, {
      endRevision: event.detail.value,
    }));
  }

  async onBugId_(event) {
    await STORE.dispatch(UPDATE(this.statePath, {bugId: event.detail.value}));
  }

  async onModeChange_(event) {
    if (!event.detail.value) return;
    await STORE.dispatch(UPDATE(this.statePath, {mode: event.detail.value}));
  }

  async onPatch_(event) {
    await STORE.dispatch(UPDATE(this.statePath, {patch: event.detail.value}));
  }

  async onOpen_(event) {
    await STORE.dispatch(UPDATE(this.statePath, {isOpen: true}));
  }

  async onSubmit_(event) {
    try {
      STORE.dispatch(UPDATE(this.statePath, {isOpen: false, isLoading: true}));
      const request = new NewPinpointRequest({
        alerts: this.alertKeys,
        suite: this.suite,
        bot: this.bot,
        measurement: this.measurement,
        case: this.case,
        statistic: this.statistic,
        mode: this.mode,
        bugId: this.bugId,
        patch: this.patch,
        startRevision: this.startRevision,
        endRevision: this.endRevision,
      });
      const jobId = await request.response;
      STORE.dispatch(UPDATE(this.statePath, {isLoading: false, jobId}));
    } catch (err) {
      STORE.dispatch(UPDATE(this.statePath, {
        isLoading: false,
        errors: [err.message],
      }));
    }
  }
}

BisectDialog.MODE = {
  PERFORMANCE: 'performance',
  FUNCTIONAL: 'functional',
};

ElementBase.register(BisectDialog);
