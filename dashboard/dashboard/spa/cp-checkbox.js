/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {LitElement, html, css} from 'lit-element';
import {afterRender} from './utils.js';

export default class CpCheckbox extends LitElement {
  static get properties() {
    return {
      checked: {type: Boolean},
      disabled: {type: Boolean},
    };
  }

  static get styles() {
    return css`
      :host {
        align-items: center;
        display: inline-flex;
        outline: none;
        width: 100%;
      }
      :host([hidden]) {
        visibility: hidden;
      }
      label {
        align-items: center;
        cursor: pointer;
        display: inline-flex;
        height: 32px;
        position: relative;
        width: 100%;
      }
      label:before, label:after {
        content: "";
        position: absolute;
        left: -22px;
        top: 8px;
      }
      label:before {
        background: var(--background-color, white);
        border-radius: 2px;
        border: 2px solid var(--foreground-color, black);
        cursor: pointer;
        height: 18px;
        transition: background .3s;
        width: 18px;
      }
      input {
        outline: 0;
        visibility: hidden;
      }
      input:checked + label:before {
        background: var(--primary-color-dark, blue);
        border: 2px solid var(--primary-color-dark, blue);
      }
      input:checked + label:after {
        border-color: var(--background-color, white);
        border-style: none none solid solid;
        border-width: 2px;
        height: 6px;
        left: -18px;
        top: 13px;
        transform: rotate(-45deg);
        width: 12px;
      }
      input:disabled + label:before {
        border-color: var(--neutral-color-dark, darkgrey);
      }
      input:disabled:checked + label:before {
        background: var(--neutral-color-dark, darkgrey);
      }
      *, *:before, *:after {
        box-sizing: border-box;
      }
    `;
  }

  render() {
    return html`
      <input
          type="checkbox"
          id="native"
          .checked="${this.checked}"
          ?disabled="${this.disabled}"
          @change="${this.onChange_}">
      <label for="native"><slot></slot></label>
    `;
  }

  firstUpdated() {
    this.native = this.shadowRoot.querySelector('#native');
  }

  click() {
    this.native.dispatchEvent(new CustomEvent('change'));
  }

  onChange_(event) {
    this.dispatchEvent(new CustomEvent('change', {
      bubbles: true,
      composed: true,
      detail: {event},
    }));
  }
}

customElements.define('cp-checkbox', CpCheckbox);
