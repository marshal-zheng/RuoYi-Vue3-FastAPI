// HTTP feedback may arrive before the explicitly bound root Provider is ready.
export function createFeedbackChannel<Options, Result>() {
  type Sender = (options: Options) => Promise<Result>;
  let sender: Sender | undefined;
  const pending: Array<{
    options: Options;
    resolve: (result: Result) => void;
    reject: (error: unknown) => void;
  }> = [];

  function send(options: Options): Promise<Result> {
    if (sender) return sender(options);
    return new Promise((resolve, reject) => pending.push({ options, resolve, reject }));
  }

  function bind(next: Sender): () => void {
    const previous = sender;
    sender = next;
    for (const item of pending.splice(0)) {
      next(item.options).then(item.resolve, item.reject);
    }
    return () => {
      if (sender === next) sender = previous;
    };
  }

  return { send, bind };
}
