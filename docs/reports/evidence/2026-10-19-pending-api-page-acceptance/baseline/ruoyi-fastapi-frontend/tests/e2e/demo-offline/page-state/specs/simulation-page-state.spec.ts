import { expect, test } from '@playwright/test';

import { goToHashPath } from '../../fixtures';
import { attachMockNetworkRecorder } from '../../network';
import { activateOverlays, expectDemoOfflineRuntime, expectOverlayState } from '../../runtime';
import { selectors } from '../../selectors';
import { loginDemo, openRoot, seedEditableVersion, seedProject } from '../fixtures';

test.describe('demo-offline simulation page states', () => {
  test('renders readonly controls from simulation session overlay', async ({ page }) => {
    const network = attachMockNetworkRecorder(page);
    await openRoot(page, network);
    await expectDemoOfflineRuntime(page);
    await loginDemo(page, network);

    await activateOverlays(page, ['simulation-session-readonly']);
    await expectOverlayState(page, ['simulation-session-readonly']);

    network.setStep('open readonly simulation page');
    const readonlySession = network.waitForOverlayResponse('simulation-session-readonly');
    const statusResponse = network.waitForMockResponse('simulation:status');
    const messagesResponse = network.waitForMockResponse('simulation:messages');
    await goToHashPath(
      page,
      `/project/simulation/index/${seedProject.projectId}?versionId=${seedEditableVersion.versionId}`
    );
    await readonlySession;
    await statusResponse;
    await messagesResponse;

    await expect(page.getByTestId(selectors.simulation.page)).toBeVisible();
    await expect(page.getByTestId(selectors.simulation.readonlyBanner)).toContainText(
      '只读演示模式'
    );
    await expect(page.getByTestId(selectors.simulation.pause)).toBeDisabled();
    network.assertOverlayResponsesTagged();
    network.assertNoRealBackendRequests();
  });

  test('surfaces unsupported control state from a real simulation page action', async ({
    page,
  }) => {
    const network = attachMockNetworkRecorder(page);
    await openRoot(page, network);
    await expectDemoOfflineRuntime(page);
    await loginDemo(page, network);

    await activateOverlays(page, ['simulation-pause-unsupported']);
    await expectOverlayState(page, ['simulation-pause-unsupported']);

    network.setStep('open simulation page');
    const sessionResponse = network.waitForMockResponse('simulation:session:create-readonly');
    const statusResponse = network.waitForMockResponse('simulation:status');
    const messagesResponse = network.waitForMockResponse('simulation:messages');
    await goToHashPath(
      page,
      `/project/simulation/index/${seedProject.projectId}?versionId=${seedEditableVersion.versionId}`
    );
    await sessionResponse;
    await statusResponse;
    await messagesResponse;
    await expect(page.getByTestId(selectors.simulation.page)).toBeVisible();
    await expect(page.getByTestId(selectors.simulation.project)).toContainText(
      seedProject.projectName
    );
    await expect(page.getByTestId(selectors.simulation.pause)).toBeVisible();

    network.setStep('pause simulation unsupported');
    const unsupported = network.waitForOverlayResponse('simulation-pause-unsupported');
    await page.getByTestId(selectors.simulation.pause).click();
    const response = await unsupported;

    expect(response.status()).toBe(501);
    await expect(page.getByTestId(selectors.simulation.page)).toBeVisible();
    await expect(
      page.getByText(/MOCK_API_NOT_IMPLEMENTED|只读模式|不支持|暂停失败|请求失败/)
    ).toBeVisible();
    network.assertOverlayResponsesTagged();
    network.assertNoRealBackendRequests();
  });
});
