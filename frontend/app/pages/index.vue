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
        
        <div class="control">
          <select v-model="bookid">
            <option :value="null">Выберите источник поиска...</option>
            <option :value="0">Тестовая книга</option>
            <option 
              v-for="book in books"
              :key="book.id"
              :value="book.id"
            >
              {{ book.name }}
            </option>
          </select>
        </div>
        
        <div v-if="loading" class="loading">Идёт поиск...</div>
        <div v-else-if="error" class="error">{{ error }}</div>

        <div v-else-if="quotes.length > 0" class="quotes">
          <div v-for="(quote, idx) in quotes" :key="idx" class="card">
            <h2>Цитата из книги</h2>
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
import { ref, onMounted } from 'vue'

const question = ref('')
const bookid = ref(null)
const books = ref([])
const quotes = ref([])
const titles = ref([])
const loading = ref(false)
const error = ref(null)

onMounted(async () => {
  try {
    const res = await fetch('http://localhost:8000/book/library')
    if (res.ok) {
      books.value = await res.json()
    }
  } catch (e) {
    console.warn('Не удалось загрузить список книг:', e)
  }
})

async function search() {
  if (!question.value.trim()) return

  loading.value = true
  error.value = null

  try {
    const url = new URL('http://localhost:8000/search/')
    url.searchParams.append('question', question.value)
    if (bookid.value !== null && bookid.value !== '') {
      url.searchParams.append('book_id', bookid.value)
    }
    
    const res = await fetch(url)
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
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