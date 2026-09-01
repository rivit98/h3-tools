from collections import defaultdict


class HookManager:
    # TODO: needs locking?
    def __init__(self):
        # used for indexing hooks
        self.idx = 0

        # hooks[msg_type][hook_idx] = func
        # dict preserves order
        self.hooks = defaultdict(dict)

    def install_hook(self, msg_type, fn):
        self.hooks[msg_type][self.idx] = fn
        self.idx += 1

    def remove_hook(self, msg_type, idx):
        del self.hooks[msg_type][idx]

    def reset_hooks(self):
        self.hooks = defaultdict(dict)

    def remove_hook_by_idx(self, idx):
        for msg_type, hooks in self.hooks.items():
            for hook_idx in hooks.keys():
                if hook_idx == idx:
                    del self.hooks[msg_type][hook_idx]
                    return True

        return False

    def fire_hooks(self, obj):
        for hooks in self.hooks.values():
            for hook in hooks.values():
                hook(obj)
