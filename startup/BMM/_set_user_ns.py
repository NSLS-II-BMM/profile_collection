import functools
import inspect


def set_user_ns(func):
    """
    This is a 'dummy' version of `set_user_ns` from Bluesky QueueServer packgage.
    It is supposed to be used if Bluesky Queueserver is not installed. Works only
    from IPython.
    """

    def get_user_ns():
        ip = get_ipython()
        user_ns = ip.user_ns
        return ip, user_ns

    # Parameter 'ipython' is optional
    is_ipython_in_sig = "ipython" in inspect.signature(func).parameters

    if inspect.isgeneratorfunction(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ip, user_ns = get_user_ns()
            kwargs.update({"user_ns": user_ns})
            if is_ipython_in_sig:
                kwargs.update({"ipython": ip})
            yield from func(*args, **kwargs)

    else:

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ip, user_ns = get_user_ns()
            kwargs.update({"user_ns": user_ns})
            if is_ipython_in_sig:
                kwargs.update({"ipython": ip})
            return func(*args, **kwargs)

    params_to_remove = ("user_ns", "ipython")
    sig_params = inspect.signature(wrapper).parameters
    sig = inspect.Signature([sig_params[_] for _ in sig_params if _ not in params_to_remove])
    wrapper.__signature__ = sig

    return wrapper
