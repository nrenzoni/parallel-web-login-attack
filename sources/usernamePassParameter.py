class UsernamePassParameter:
    def __init__(self, username_param_name, password_param_name, username_to_try, other_params_dict=None):
        self.username_to_try = username_to_try
        self.password_param_name = password_param_name
        self.username_param_name = username_param_name
        if other_params_dict is None:
            self.other_params_dict = {}
        else:
            self.other_params_dict = other_params_dict

    def gen_param_dict(self, password):
        # ** operator on dict spreads dict into another dict
        return {self.username_param_name: self.username_to_try, self.password_param_name: password,
                **self.other_params_dict}

    def findElem(self, match_str):
        for p in self.other_params_dict:
            if match_str in p:
                return p
        raise Exception("{} not found in param_lst".format(match_str))
