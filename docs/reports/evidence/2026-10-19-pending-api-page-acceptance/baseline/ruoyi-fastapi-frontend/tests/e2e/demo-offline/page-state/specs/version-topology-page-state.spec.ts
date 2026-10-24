import { expect, test } from '@playwright/test';

import {
  fillByTestId,
  goToHashPath,
  submitVisibleDialog,
  testId,
  uniqueName,
} from '../../fixtures';
import { attachMockNetworkRecorder } from '../../network';
import { activateOverlays, expectDemoOfflineRuntime, expectOverlayState } from '../../runtime';
import { selectors } from '../../selectors';
import {
  loginDemo,
  openProjectDetail,
  openRoot,
  seedEditableVersion,
  seedProject,
} from '../fixtures';

test.describe('demo-offline version and topology page states', () => {
  test('renders version list empty state through runtime overlay activation', async ({ page }) => {
    const network = attachMockNetworkRecorder(page);
    await openRoot(page, network);
    await expectDemoOfflineRuntime(page);
    await loginDemo(page, network);

    await activateOverlays(page, ['version-list-empty']);
    await expectOverlayState(page, ['version-list-empty']);
    const versionEmpty = network.waitForOverlayResponse('version-list-empty');
    await openProjectDetail(page, network);
    await versionEmpty;

    await expect(page.getByTestId('version-list-empty')).toBeVisible();
    await expect(page.getByTestId(selectors.version.list)).toBeVisible();
    network.assertOverlayResponsesTagged();
    network.assertNoRealBackendRequests();
  });

  test('keeps version clone dialog open on forbidden overlay', async ({ page }) => {
    const network = attachMockNetworkRecorder(page);
    await openRoot(page, network);
    await expectDemoOfflineRuntime(page);
    await loginDemo(page, network);
    await openProjectDetail(page, network);

    await activateOverlays(page, ['version-clone-forbidden']);
    await expectOverlayState(page, ['version-clone-forbidden']);

    await page.getByTestId(selectors.version.clone(seedEditableVersion.versionId)).click();
    await fillByTestId(page, 'version-clone-number', uniqueName('V-403'));
    await fillByTestId(page, 'version-clone-name', '禁止克隆版本');

    network.setStep('clone version forbidden');
    const cloneForbidden = network.waitForOverlayResponse('version-clone-forbidden');
    await submitVisibleDialog(page, /克隆版本/, /克隆/);
    const response = await cloneForbidden;

    expect(response.status()).toBe(403);
    await expect(page.getByRole('dialog', { name: /克隆版本/ })).toBeVisible();
    await expect(page.getByTestId(selectors.version.cloneError)).toContainText(
      '当前用户无权克隆项目版本'
    );
    network.assertOverlayResponsesTagged();
    network.assertNoRealBackendRequests();
  });

  test('keeps topology editor visible when save fails through overlay', async ({ page }) => {
    const network = attachMockNetworkRecorder(page);
    await openRoot(page, network);
    await expectDemoOfflineRuntime(page);
    await loginDemo(page, network);

    await activateOverlays(page, ['topology-save-500']);
    await expectOverlayState(page, ['topology-save-500']);

    network.setStep('open topology editor');
    const topologyGet = network.waitForMockResponse('project:topology:get');
    const deviceList = network.waitForMockResponse('device:list');
    await goToHashPath(
      page,
      `/project/topo/index/${seedProject.projectId}?versionId=${seedEditableVersion.versionId}`
    );
    await topologyGet;
    await deviceList;
    await page
      .locator(`${testId(selectors.topology.canvas)} .x6-node`)
      .first()
      .waitFor();

    network.setStep('save topology error');
    const saveError = network.waitForOverlayResponse('topology-save-500');
    await page.getByTestId(selectors.topology.save).click();
    const response = await saveError;

    expect(response.status()).toBe(500);
    await expect(page.getByTestId(selectors.topology.page)).toBeVisible();
    await expect(page).toHaveURL(/#\/project\/topo\/index\/1001/);
    network.assertOverlayResponsesTagged();
    network.assertNoRealBackendRequests();
  });

  test('shows and clears topology loading state for latency overlay', async ({ page }) => {
    const network = attachMockNetworkRecorder(page);
    await openRoot(page, network);
    await expectDemoOfflineRuntime(page);
    await loginDemo(page, network);

    await activateOverlays(page, ['topology-load-latency']);
    await expectOverlayState(page, ['topology-load-latency']);

    network.setStep('open topology editor with latency');
    const topologyLatency = network.waitForOverlayResponse('topology-load-latency');
    const deviceList = network.waitForMockResponse('device:list');
    await goToHashPath(
      page,
      `/project/topo/index/${seedProject.projectId}?versionId=${seedEditableVersion.versionId}`
    );
    await expect(page.getByTestId(selectors.topology.loading)).toBeVisible();
    await topologyLatency;
    await expect(page.getByTestId(selectors.topology.loading)).toBeHidden();
    await deviceList;
    await page
      .locator(`${testId(selectors.topology.canvas)} .x6-node`)
      .first()
      .waitFor();
    network.assertOverlayResponsesTagged();
    network.assertNoRealBackendRequests();
  });
});
