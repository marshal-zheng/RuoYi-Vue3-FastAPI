import { beforeEach, describe, expect, it, vi } from 'vitest';

const messageSuccess = vi.fn();
const messageError = vi.fn();
const notificationInfo = vi.fn();
const notificationWarning = vi.fn();
const notificationError = vi.fn();
const resolveFeedbackRegistryEntry = vi.fn();

vi.mock('element-plus', () => ({
  ElMessage: {
    success: messageSuccess,
    error: messageError,
  },
  ElNotification: {
    info: notificationInfo,
    warning: notificationWarning,
    error: notificationError,
  },
}));

vi.mock('@/utils/feedback/registry', () => ({
  resolveFeedbackRegistryEntry,
}));

describe('feedback presenter', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resolveFeedbackRegistryEntry.mockReturnValue({ success: '操作成功' });
  });

  it('defaults feedback options to silent mode', async () => {
    const { resolveFeedbackOptions } = await import('@/utils/feedback/presenter');

    expect(resolveFeedbackOptions()).toEqual({
      mode: 'silent',
      key: undefined,
      successContext: {},
      validationTarget: undefined,
    });
  });

  it('shows registry success message for auto success feedback', async () => {
    resolveFeedbackRegistryEntry.mockReturnValue({ success: '新增用户成功' });
    const { presentSuccessFeedback } = await import('@/utils/feedback/presenter');

    presentSuccessFeedback({
      status: 201,
      payload: { id: 1 },
      meta: { status: 201 },
      feedback: {
        mode: 'auto',
        key: 'system.user.create',
        successContext: {},
      },
    });

    expect(messageSuccess).toHaveBeenCalledWith('新增用户成功');
  });

  it('uses notification info for accepted responses', async () => {
    resolveFeedbackRegistryEntry.mockReturnValue({
      success: 'ignored',
      accepted: '任务已受理，可稍后查看执行结果',
    });
    const { presentSuccessFeedback } = await import('@/utils/feedback/presenter');

    presentSuccessFeedback({
      status: 202,
      payload: { jobId: 1 },
      meta: { status: 202, location: 'https://api.example.test/jobs/1' },
      feedback: {
        mode: 'auto',
        key: 'monitor.job.run',
        successContext: {},
      },
    });

    expect(notificationInfo).toHaveBeenCalledWith(
      expect.objectContaining({
        title: '已受理',
        message: '任务已受理，可稍后查看执行结果',
      })
    );
  });

  it('uses warning notification for partial batch success', async () => {
    const { presentSuccessFeedback } = await import('@/utils/feedback/presenter');

    presentSuccessFeedback({
      status: 200,
      payload: {
        results: [{ success: true }, { success: false }],
        summary: { total: 2, succeeded: 1, failed: 1 },
      },
      meta: { status: 200 },
      feedback: {
        mode: 'auto',
        key: 'protocol.protocol.delete-batch',
        successContext: {},
      },
    });

    expect(notificationWarning).toHaveBeenCalledWith(
      expect.objectContaining({
        title: '部分完成',
        message: '共 2 项，成功 1 项，失败 1 项',
      })
    );
    expect(messageSuccess).not.toHaveBeenCalled();
  });

  it('maps 422 validation problems to the validation target', async () => {
    const apply = vi.fn();
    const { presentProblemFeedback } = await import('@/utils/feedback/presenter');

    presentProblemFeedback({
      problem: {
        type: 'https://problems.test/validation-error',
        title: '参数验证失败',
        status: 422,
        detail: '请检查输入字段',
        instance: '/system/user',
        errors: [{ field: 'userName', message: '不能为空', code: 'missing' }],
      },
      meta: { status: 422 },
      feedback: {
        mode: 'auto',
        key: 'system.user.create',
        successContext: {},
        validationTarget: { apply },
      },
    });

    expect(apply).toHaveBeenCalledWith([
      { field: 'userName', message: '不能为空', code: 'missing' },
    ]);
    expect(notificationError).not.toHaveBeenCalled();
  });

  it('shows rate limit details with tracking identifiers', async () => {
    const { presentProblemFeedback } = await import('@/utils/feedback/presenter');

    presentProblemFeedback({
      problem: {
        type: 'https://problems.test/rate-limit',
        title: '请求过于频繁',
        status: 429,
        detail: '请稍后再试',
        instance: '/monitor/job/run',
        requestId: 'req-1',
      },
      meta: {
        status: 429,
        retryAfter: 30,
        traceId: 'trace-1',
      },
      feedback: {
        mode: 'auto',
        key: 'monitor.job.run',
        successContext: {},
      },
    });

    expect(notificationWarning).toHaveBeenCalledWith(
      expect.objectContaining({
        title: '请求过于频繁',
        message: expect.stringContaining('请在 30 秒后重试'),
      })
    );
    expect(notificationWarning.mock.calls[0][0].message).toContain('Request ID: req-1');
    expect(notificationWarning.mock.calls[0][0].message).toContain('Trace ID: trace-1');
  });
});
