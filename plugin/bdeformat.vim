if has("python")
    py from bdeformatvimadapter import formatBde

    command! BDEFormat :py formatBde()
endif
