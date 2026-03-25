<template>
    <div>
        <Header>
            <h1>Чудопоиск</h1>
        </Header>
        <div class="control">
            <input
                v-model="question"
                type="text"
                name="question"
                id="question"
                placeholder="Введите свой вопрос..."
                @keyup.enter="search"
            >
            <a href="/books">
                <img src="~/assets/images/book.svg" alt="Книга">
            </a>
        </div>
        <div v-if="loading" class="loading">Идёт поиск...</div>

        <div v-else-if="error" class="error">{{ error }}</div>

        <div v-else-if="quotes.length > 0" class="quotes">
          <div v-for="(quote, idx) in quotes" :key="idx" class="card">
            <h2>{{ titles[idx] }}</h2>
            <p>{{ quote }}</p>
          </div>
        </div>

        <div v-else class="quotes">
          <div class="card">
            <h2>Ничего не найдено</h2>
            <p>Введите вопрос, чтобы найти цитаты из книг.</p>
          </div>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue'

const question = ref('')
const quotes = ref([])
const titles = ref([])
const loading = ref(false)
const error = ref(null)

async function search() {
  if (!question.value.trim()) return

  loading.value = true
  error.value = null

  try {
    const res = await fetch(`http://localhost:8000/search/?question=${encodeURIComponent(question.value)}`)
    if (!res.ok) {
      const errData = await res.json()
      throw new Error(errData.detail?.[0]?.msg || `HTTP ${res.status}`)
    }
    const data = await res.json()
    quotes.value = data.quotes || []
    titles.value = data.titles || []
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>