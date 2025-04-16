from src.whitehat import create_account, Registration

reg = Registration.find_by_id('64ed06315db7536320ecac12')

create_account(reg)