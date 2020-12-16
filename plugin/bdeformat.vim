if has("python3")
    py3 from bdeformatvimadapter import formatBde

    command! BDEFormat :py3 formatBde()
endif
